import json
import twitter
import os
import sys
import re

from colorama import Fore, Style

print(f'working in {os.getcwd()}')
if not os.path.exists('grid/adapters/config.json'):
    print(f'{Fore.RED}no {Fore.YELLOW}config.json{Fore.RED} file present in adapters directory.  Make sure the file exists{Style.RESET_ALL}')
    sys.exit()

config = json.load(open('grid/adapters/config.json'))

if not 'consumerKey' in config.keys():
    print(f'{Fore.RED}no {Fore.YELLOW}consumerKey{Fore.RED} specified in config.json.  Check {Fore.YELLOW}config.example.json{Fore.RED} for an example{Style.RESET_ALL}')
    sys.exit()
if not 'consumerSecret' in config.keys():
    print(f'{Fore.RED}no {Fore.YELLOW}consumerSecret{Fore.RED} specified in config.json.  Check {Fore.YELLOW}config.example.json{Fore.RED} for an example{Style.RESET_ALL}')
    sys.exit()
if not 'accessTokenKey' in config.keys():
    print(f'{Fore.RED}no {Fore.YELLOW}accessTokenKey{Fore.RED} specified in config.json.  Check {Fore.YELLOW}config.example.json{Fore.RED} for an example{Style.RESET_ALL}')
    sys.exit()
if not 'accessTokenSecret' in config.keys():
    print(f'{Fore.RED}no {Fore.YELLOW}accessTokenSecret{Fore.RED} specified in config.json.  Check {Fore.YELLOW}config.example.json{Fore.RED} for an example{Style.RESET_ALL}')
    sys.exit()

def next_input():
    api = twitter.Api(consumer_key=config['consumerKey'],
        consumer_secret=config['consumerSecret'],
        access_token_key=config['accessTokenKey'],
        access_token_secret=config['accessTokenSecret'])

    statuses = api.GetUserTimeline(screen_name='gavinuhma')

    #wordmap, hashtagmap = build_vocab(tweets)

    #input, target = build_embedding_tensors(tweets, wordmap, hashtagmap)

    #print(input[:5])
    #print(target[:5])

    return statuses[0]


hashtag_re = re.compile('(?:^|\s)[＃#]{1}(\w+)', re.UNICODE)
regex = re.compile('[^a-zA-Z]')


def normalize_word(word):
    alpha = regex.sub('', word)

    if "http" in alpha:
        return ''
    else:
        return alpha.lower()


def find_hashtags(tweet):
    hashtags = hashtag_re.findall(tweet)

    lower_hash = []

    for hashtag in hashtags:
        lower_hash.append(hashtag.lower())

    return lower_hash


def remove_hashtags(tweet):
    removed = hashtag_re.sub('', tweet)

    return removed


def build_vocab(tweets):
    wordlist = []
    hashtags = []

    for tweet in tweets:
        if "text" in tweet:
            no_hashtags = remove_hashtags(tweet['text'])
            htgs = find_hashtags(tweet['text'])
            if htgs:
                hashtags.extend(htgs)

            split = no_hashtags.split(' ')

            for word in split:
                normalized = normalize_word(word)

                if normalized != '':
                    wordlist.append(normalized)

    # remove dups
    wordset = set(wordlist)
    hashtagset = set(hashtags)

    wordmap = dict()
    hashtagmap = dict()

    i = 0
    for word in wordset:
        wordmap[word] = i
        i += 1

    i = 0
    for hashtag in hashtagset:
        hashtagmap[hashtag] = i
        i += 1

    return wordmap, hashtagmap


def build_embedding_tensors(tweets, wordmap, hashtagmap):
    input = []
    target = []
    for tweet in tweets:
        wl = []
        if "text" in tweet:
            no_hashtags = remove_hashtags(tweet['text'])
            hashtags = find_hashtags(tweet['text'])
            if not hashtags:
                continue

            split = no_hashtags.split(' ')

            for word in split:
                normalized = normalize_word(word)

                if normalized != '':
                    wl.append(normalized)

        for word in wl:
            for hashtag in hashtags:
                word_i = wordmap[word]
                hashtag_i = hashtagmap[hashtag]

                input.append(word_i)
                target.append(hashtag_i)

    return input, target
