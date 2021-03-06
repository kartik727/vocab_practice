from PyDictionary import PyDictionary as pdict
import pandas as pd
from tqdm import tqdm
import argparse

def get_meaning(word):
    meaning = pdict.meaning(word)
    df = pd.DataFrame.from_dict(meaning, orient='index')
    return df

def get_list_meanings(words:list, old_data_path:str, reset:bool=False, verbose:bool=False)->pd.DataFrame:
    '''
    Returns a DataFrame of words and their meanings by updating the existing table with new words provided to the function.
    '''
    if not reset:
        old_df = pd.read_csv(old_data_path, index_col=['Word', 'Type'])
        old_words = set(old_df.index.get_level_values(0))
        new_words = [word for word in words if word not in old_words]
    else:
        new_words = words
        print('Old data has been reset.')

    print(f'Number of new words: {len(new_words)}')

    meanings = {}
    for word in tqdm(new_words, desc='Processing words'):
        try:
            meaning = get_meaning(word)
            meanings[word] = meaning
        except TypeError:
            print(f'Could not find {word}')

    if len(meanings)>0:
        df = pd.concat(meanings)
        df.index.set_names(['Word', 'Type'], inplace=True)
        total_cols = len(df.columns)
        df.columns = [f'Meaning {i+1}' for i in range(total_cols)]

        if verbose:
            print(meanings)

        if not reset:
            df = pd.concat([old_df, df])

        df.fillna('', inplace=True)
    else:
        df = old_df

    print('Process completed successfully.')

    return df

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--reset', action='store_true', help='Remove all current words and build dictionary from scratch')
    parser.add_argument('-w', '--add-words', nargs='+', default=[], help='Terminal option to specify words', metavar='')
    parser.add_argument('--terminal-only', action='store_true', help='Use words only from terminal, ignoring words file')
    parser.add_argument('-v', '--verbose', action='store_true', help='Print the results for newly added words')
    parser.add_argument('--word-filename', default='words.csv', help='Give the name of the file to add words', metavar='')
    parser.add_argument('--save-filename', default='meanings.csv', help='Give the name of the file to save final meanings', metavar='')
    args = parser.parse_args()

    data_path = 'data/' + args.word_filename
    save_path = 'data/' + args.save_filename

    reset_flag = args.reset
    if reset_flag:
        confirmation_msg = 'Reset the data file'
        response = input(f'You are about to reset the file containing words and meanings. To confirm type `{confirmation_msg}`.\n')
        if response == confirmation_msg:
            print('Reset confirmed.')
        else:
            print('Incorrect confirmation response. Aborting.')
            reset_flag = False

    if args.terminal_only:
        words = args.add_words
    else:
        words = list(pd.read_csv(data_path, on_bad_lines='skip')['Word']) + args.add_words

    meanings = get_list_meanings(words, save_path, reset=reset_flag, verbose=args.verbose)
    meanings.to_csv(save_path)

if __name__ == '__main__':
    main()