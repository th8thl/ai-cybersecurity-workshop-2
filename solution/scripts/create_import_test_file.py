"""Create a harmless test file for the application's ticket-import route."""
from pathlib import Path
import pickle


class PrintWhenRead:
    def __reduce__(self):
        # Reconstructing this object calls print. No file, network or OS actions.
        return print, ('FILE_IMPORT_EXECUTED_CODE',)


def pickle_test_file():
    return pickle.dumps(PrintWhenRead())


if __name__ == '__main__':
    destination = Path(__file__).resolve().parents[1] / 'results' / 'import-test.pkl'
    destination.parent.mkdir(exist_ok=True)
    destination.write_bytes(pickle_test_file())
    print(f'Created {destination}')
    print('Upload this file through Import a ticket file. Watch the website terminal.')
    print('If FILE_IMPORT_EXECUTED_CODE appears there, the application executed Python from the uploaded file.')
