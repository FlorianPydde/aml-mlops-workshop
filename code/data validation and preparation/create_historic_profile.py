"""
Script the creation of the historic  profile, we use the historic profiles to
see and monitor how our data is changing over time. In this senario we assume
that data is loaded every day. This is the profile we automatically train
(every day) from a trigger from cloud with cloud data (pipeline-step)
-----------------------------
- report basic statistics
- SME knowledge data
- use report for over-time changes as well
"""
# load packeges.
import pandas as pd
import string
import nltk
import numpy as np
from collections import Counter
from nltk.corpus import stopwords
from textblob import TextBlob
from datetime import date, timedelta
import argparse
import os
from azureml.core import Datastore
import csv
from azureml.core import Run
from packages import plots
from packages.get_data import load_data

parser = argparse.ArgumentParser()
parser.add_argument('--data_folder',
                    type=str,
                    default=os.path.join(
                     os.path.dirname(os.path.realpath(__file__)),
                     "../..",
                     "outputs/raw_data/raw_subset_train.csv",
                    ),
                    dest='data_folder',
                    help='data folder mounting point')
parser.add_argument('--profile_folder',
                    type=str,
                    default=os.path.join(
                     os.path.dirname(os.path.realpath(__file__)),
                     "../..",
                     "outputs/historic_profile/historic_profile.csv",
                    ),
                    dest='profile_folder',
                    help='profile folder mounting point')
parser.add_argument('--word_profile_folder',
                    type=str,
                    default=os.path.join(
                     os.path.dirname(os.path.realpath(__file__)),
                     "../..",
                     "outputs/historic_profile/historic_word_profile.csv",
                    ),
                    dest='word_profile_folder',
                    help='word profile folder mounting point')
parser.add_argument('--new_profile',
                    type=str,
                    default='no',
                    help='indicator to create new profile')
parser.add_argument('--local',
                    type=str,
                    default='yes')
parser.add_argument("--input_train",
                    type=str)
parser.add_argument('--historicprofile',
                    type=str)

opts = parser.parse_args()
try:
    path = os.environ.get("AZUREML_DATAREFERENCE_historicProfile")

    opts.profile_folder = path + '/' + "historic_profile.csv"
    opts.word_profile_folder = path + '/' + "historic_word_profile.csv"
    print("Downloaded historic profile from cloud")
except IOError:
    print("no file present")
except TypeError:
    print("no file present")

if not (opts.input_train is None):
    data = pd.read_csv(
        os.path.join(
            opts.input_train + '_validated.csv'
        ),
        lineterminator='\n'
    )
    print("Data downsloaded from cloud")

# Get run context
run = Run.get_context()

# create outputs folder
OUTPUTSFOLDER = 'outputs/historic_profile'
# create outputs folder if not exists

if not os.path.exists(OUTPUTSFOLDER):
    os.makedirs(OUTPUTSFOLDER)

nltk.download('stopwords')
stop = stopwords.words('english')

today = str(date.today() + + timedelta(days=49))
#today = str(date.today())
print(today)

if opts.input_train is None:
    if opts.local == 'yes':
        path = opts.data_folder
        print(path)
    else:
        print(opts.data_folder)
        print(os.listdir(opts.data_folder))
        try:
            subsubpath = opts.data_folder + '/workspaceblobstore'
            dir_list_1 = os.listdir(subsubpath)
            subpath = opts.data_folder + '/workspaceblobstore/' + dir_list_1[0]
            df = []
            dir_list = os.listdir(
                subpath
                )
            for week in dir_list:
                print("weeks in dataset:", week)
                sub_list = os.listdir(subpath + '/' + week)
                path = os.path.join(subpath, str(week) + '/' + sub_list[0])
                dataset_train = pd.read_csv(os.path.join(path), lineterminator='\n')
                df.append(dataset_train)
            data = pd.concat(df, ignore_index=True)
            print(len(data))
        except FileNotFoundError:
            print("one week present")
            subsubpath = opts.data_folder
            print(subsubpath)
            dir_list_1 = os.listdir(subsubpath)
            print(dir_list_1)
            df = []
            for csvfile in dir_list_1:
                path = subsubpath + '/' + csvfile
                dataset_train = pd.read_csv(os.path.join(path), lineterminator='\n')
                df.append(dataset_train)
            data = pd.concat(df, ignore_index=True)
    # import data
    print("loading data from from storage")
    data = pd.read_csv(
        os.path.join(path),
        lineterminator='\n'
    )
    print("Data downloaded")

data.columns.values[-1] = 'target'

# clean data
data.text = data.text.apply(lambda x: x.lower())
translator = str.maketrans('', '', string.punctuation)
data.text = data.text.apply(
    lambda x: x.translate(translator))
data.text = data.text.apply(
    lambda x: x.translate(string.digits))

# Classes balance + std
classes = data.target.value_counts(normalize=True)
data_mean = classes.mean()
data_std = classes.std()
print("Average mean is:", data_mean)
print("Average standard deviation is:", data_std)


# avg word length
def avg_word(sentence):
    words = sentence.split()
    return (sum(len(word) for word in words)/len(words))


data['avg_word'] = data['text'].apply(lambda x: avg_word(x))
mean_avg_word = data['avg_word'].mean()
print("Avarage word length is:", mean_avg_word)

# avg number of stop words
data['stopwords'] = data['text'].apply(
    lambda x: len([x for x in x.split() if x in stop])
    )
mean_stopwords = data['stopwords'].mean()
print("Average number of stop words is:",  mean_stopwords)

# setiment analyse
data['sentiment'] = data['text'].apply(
    lambda x: TextBlob(x).sentiment[0]
    )
mean_sentiment = data['sentiment'].mean()
print("average sentiment is:",  mean_sentiment)

lst = []
lst1 = []
# creat df for profiling for 1st time:
if opts.new_profile == 'yes':
    print("creating new profile")
    values = {
        'date': [today],
        'mean of classes':  [data_mean],
        'standard deviation of classes': [data_std],
        'average word length': [mean_avg_word],
        'average number of stopwords': [mean_stopwords],
        'average sentiment': [mean_sentiment]
    }

    profile = pd.DataFrame(
        values,
        columns=[
            'date',
            'mean of classes',
            'standard deviation of classes',
            'average word length',
            'average number of stopwords',
            'average sentiment'
        ],
        )
if opts.new_profile == 'no':
    profile = pd.DataFrame()
    new_profile = pd.read_csv(os.path.join(opts.profile_folder), lineterminator='\n')
    print("Downloaded file", new_profile)
    int_profile = new_profile.drop(new_profile.columns[[0]], axis=1)
    print("Downloaded file", int_profile)
    values = {
        'date': [today],
        'mean of classes':  [data_mean],
        'standard deviation of classes': [data_std],
        'average word length': [mean_avg_word],
        'average number of stopwords': [mean_stopwords],
        'average sentiment': [mean_sentiment]
    }

    prof = pd.DataFrame(
        values,
        columns=[
            'date',
            'mean of classes',
            'standard deviation of classes',
            'average word length',
            'average number of stopwords',
            'average sentiment'
        ],
        )
    profile = int_profile.append(prof, ignore_index=True)

print("new profile", profile)
for index in range(len(profile)):
    run.log_row("profile",
                date=profile.iloc[index, 0],
                mean_of_classes=profile.iloc[index, 1],
                standard_deviation=profile.iloc[index, 2],
                word_lengt=profile.iloc[index, 3],
                average_nummber_of_stop_words=profile.iloc[index, 4],
                average_sentiment=profile.iloc[index, 5])

# get words first
data_clean = data['text'].apply(
    lambda x: ' '.join([word for word in x.split() if word not in (stop)])
    )
df2 = pd.DataFrame()
df1 = pd.DataFrame()

# create dataframe
print("start word count")
print("This may take a while")
for classes in range(0, 4):
    print("Class number:", classes)
    vocab = Counter()
    df_train = data_clean[data.target == classes]
    for text in df_train:
        for word in text.split(' '):
            vocab[word.lower()] += 1

    word1 = 'word' + str(classes)
    count = 'count' + str(classes)
    idf = 'idf' + str(classes)
    tfidf = 'tfidf' + str(classes)

    df = pd.DataFrame(list(vocab.items()), columns=[word1, count])

    for i, word in enumerate(df[word1]):
        df.loc[i, idf] = np.log(df_train.shape[0] /
                                (len(df_train[df_train.str.contains(word)])))

    array = df[count] * df[idf]
    df[tfidf] = array

    df1 = df.sort_values(tfidf, ascending=False, ignore_index=True)
    df2[word1] = df1[word1]
    df2[tfidf] = df1[tfidf]

most_importantwords = df2.iloc[0:20]
most_importantwords.columns = [
    'alt.atheism', 'tfidf1',
    'talk.religion.misc', 'tfidf2',
    'comp.graphics', 'tfidf3',
    'sci.space', 'tfidf4'
    ]

lst1 = most_importantwords.values.T.tolist()
print("word count completed")

print("Historic profile created succesfully")

# save profile to local file
print("writing profile to temp file")
profile.to_csv(
    path_or_buf=os.path.join(
        OUTPUTSFOLDER,
        'historic_profile.csv')
    )

csvfile = os.path.join(
            OUTPUTSFOLDER,
            'historic_word_profile.csv'
          )

# Assuming res is a list of lists
with open(csvfile, 'a+') as output:
    writer = csv.writer(output, lineterminator='\n')
    writer.writerows([lst1])

if opts.local == 'no':
    print("uploading files to cloud")
    datastore_name = 'workspaceblobstore'
    workspace = run.experiment.workspace
    # retrieve an existing datastore in the workspace by name
    datastore = Datastore.get(workspace, datastore_name)

    # upload profile to blob
    datastore.upload(
        src_dir=os.path.join(
            OUTPUTSFOLDER
        ),
        target_path="historic_profile",
        overwrite=True,
        show_progress=True
    )

# plot profile
mean_classes = plots.plot_mean_of_classes(profile)
run.log_image("Mean of classes over time ", plot=mean_classes)
std_classes = plots.plot_std_of_classes(profile)
run.log_image("Standard deviation over time ", plot=std_classes)
avg_word_length = plots.plot_average_word_length(profile)
run.log_image("Average word length over time ", plot=avg_word_length)
avg_stop_words = plots.plot_average_number_of_stopwords(profile)
run.log_image("Average stop word over time ", plot=avg_stop_words)

if not (opts.historicprofile is None):
    os.makedirs(opts.historicprofile, exist_ok=True)
    path = opts.historicprofile + "/" + 'historic_profile.csv'
    write_df = profile.to_csv(path)
