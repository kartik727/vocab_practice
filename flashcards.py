import pandas as pd
import argparse

LEARN_THRESHOLD = 5

class LearningOverException(Exception):
    pass

def flashcards_(card: pd.Series, fc_df: pd.DataFrame, n_meanings: int) -> None:
    print(card['Word'])
    print(card['Type'])

    try:
        correct = input('Press Enter to show meaning\n')

        for n in range(n_meanings):
            m = f'Meaning {n+1}'
            if not pd.isna(card[m]):
                print(f'{m} : {card[m]}')
            else:
                break

        print()

        try:
            correct = int(correct)
        except ValueError:
            correct = ''

        if correct=='':
            input_received = False
            correct = input('Press 0 for incorrect, any other number for correct.\n')

            while not input_received:
                try:
                    correct = int(correct)
                    input_received = True
                except ValueError:
                    correct = input('Invalid input. Please enter an integer value.\n')

        correct = bool(correct)

        try:
            fc_row = fc_df.loc[(card['Word'], card['Type']), :]
        except KeyError:
            fc_row = {'count' : 0, 'current' : 0, 'status' : 0}

        fc_row['count'] += 1
        fc_row['current'] = fc_row['current'] + 1 if correct else 0

        assert fc_row['current'] >= 0, 'Something is wrong. Current underflow.'

        if fc_row['current'] == 0:
            fc_row['status'] = -1
        elif fc_row['current'] > LEARN_THRESHOLD:
            fc_row['status'] = 1
        else:
            fc_row['status'] = 0

        fc_df.loc[(card['Word'], card['Type']), :] = fc_row

    except KeyboardInterrupt:
        print('Cancelled.')
        raise LearningOverException

    finally:
        print('\n' + '-'*80 + '\n')

def flashcards(df: pd.DataFrame, fc_df: pd.DataFrame) -> None:
    n_meanings = len(df.columns) - 2

    try:
        for idx, flashcard in df.iterrows():
            flashcards_(flashcard, fc_df, n_meanings)
    except LearningOverException:
        print('Learning Over.')


def main():
    parser = argparse.ArgumentParser()
    args = parser.parse_args()

    save_path = 'data/meanings.csv'
    data_path ='data/flashcard_data.csv'

    df = pd.read_csv(save_path)
    df = df.sample(frac=1.)
    fc_df = pd.read_csv(data_path, index_col=['Word', 'Type'])

    flashcards(df, fc_df)

    fc_df.to_csv(data_path)

    print('All done. Nice.')

if __name__ == '__main__':
    main()