import os
import sys
import shutil
from zipfile import ZipFile
from termcolor import cprint
from datetime import datetime

import pandas as pd
from pandas.errors import EmptyDataError, ParserError


def name_normalize(name):
    '''
    Replaces "/" characters with "-" to 
    '''
    if name is None:
        return name

    return name.replace('/', '-')


def load_specifications(path):
    '''
    Loads in the specs.csv file using pandas and checks that it has the necesary columns.
    Returns the specs as a pandas dataframe.
    '''
    try:
        specs = pd.read_csv(path + '/specs.csv', dtype={'Section': 'str'})
    except IOError as error:
        cprint('\nError loading CSV:', 'red')
        cprint(f'{error}\n', 'red', attrs=['dark'])
        sys.exit()
    except ParserError:
        cprint('\nERROR: Could not parse specs.csv, ensure correctly formatted.', 'red')
        sys.exit()
    except EmptyDataError:
        cprint('\nERROR: Ensure specs.csv has data.', 'red')
        sys.exit()

    expected_cols = {'Course', 'Section', 'Instructor', 'Title', 'Top Slate',
                     'Body', 'Watermark', 'Watermark Position', 'Source URL'}

    actual_cols = set(list(specs))

    # Check that we have all the columns we expect
    if expected_cols != actual_cols:
        cprint('\nERROR: Missing or incorrect columns in specs.csv', 'red')
        cprint(f'Expected columns: {expected_cols}\n')
        sys.exit()

    return specs


def get_video_attributes(row):
    '''
    Loads the cell values from the dataframe row into a dictionary
    Performs a series of checks to ensure values math certain expected criteria (described below) 
    '''

    course = __parse_value(row['Course'])
    section = __parse_value(row['Section'])
    instructor = __parse_value(row['Instructor'])
    title = __parse_value(row['Title'])
    top_slate = __parse_value(row['Top Slate'])
    body = __parse_value(row['Body'])
    watermark = __parse_value(row['Watermark'])
    wm_pos = __parse_value(row['Watermark Position'])
    src_url = __parse_value(row['Source URL'])

    # These three values are used to make filepaths therefore cannot contain "/"
    course = name_normalize(course)
    instructor = name_normalize(instructor)
    title = name_normalize(title)

    # Course, Section, Instructor, Title, Top Slate must be included at minimum
    if title is None:
        cprint(
            '\nERROR: Spec must include at least a title',
            'red')
        raise ValueError()

    if section is not None and course is None:
        cprint(
            '\nERROR: A row cannot specify section code without course code (specs.csv)', 'red')
        raise ValueError

    # if top slate is specified must finish with mp4
    if top_slate is not None and str(top_slate)[-4:] != '.mp4':
        cprint('\nERROR: Must include value for slate that ends in .mp4', 'red')
        raise ValueError()

    if len(title) > 45:
        cprint('\nERROR: Does not support titles with more than 45 characters', 'red')
        raise ValueError()

    # instructor name(s) must not exceed 50 characters
    if instructor is not None and len(instructor) > 50:
        cprint(
            '\nERROR: Does not support instructor name(s) with more than 50 characters', 'red')
        raise ValueError()

    # body must finish with .mp4 (if included)
    if body is not None and body[-4:] != '.mp4':
        cprint('\nERROR: If body is included, csv value must end in .mp4', 'red')
        raise ValueError()

    # watermark must end in .png
    if watermark is not None and watermark[-4:] != '.png':
        cprint('\nERROR: If watermark included, csv value must end in .png', 'red')
        raise ValueError()

    return {
        'course': course,
        'section': section,
        'instructor': instructor,
        'title': title,
        'top_slate': top_slate,
        'body': body,
        'watermark': watermark,
        'src_url': src_url,
        'wm_pos': wm_pos
    }


def __parse_value(val):
    '''
    Returns the value if it passess value check
    Otherwise returns None
    '''
    return val if has_value(val) else None


def has_value(cell):
    """Checks if a cell value from a Pandas dataframe is a valid string

    The following are treated as invalid:
    * empty cell (None)
    * empty string ('')
    * zero (0)
    * type = nan OR type = None
    * 'null' OR 'NULL'
    * 'none' OR 'NONE'

    Args:
        cell (Any): Value of a cell from pandas dataframe

    Returns:
        Boolean: Whether or not value is valid string
    """

    # Falsy values are FALSE
    if not cell:
        return False

    # nan values FALSE
    if not isinstance(cell, str):
        return False

    # strings == 'none' or 'null' or '0' are also FALSE
    if (cell.lower() == 'none' or cell.lower() == 'null' or
            cell.lower() == 'nan' or cell == '0'):
        return False

    return True


def archive_folder_contents(folder_path):
    '''
    Zips all existing folders into file titled by the curent datetime
    Writes to archive folder
    '''
    file_paths = __get_all_file_paths(folder_path)

    now = datetime.now().strftime('%Y-%m-%dT%H.%M.%S')
    output_filename = f'{now}.zip'

    archive_folder = f'{folder_path}/archive'
    if not os.path.exists(archive_folder):
        os.makedirs(archive_folder)

    with ZipFile(f'{archive_folder}/{output_filename}', 'w') as zip:
        # writing each file one by one
        for file in file_paths:
            zip.write(file, file)

    cprint(
        f'Previous contents successfully zipped to: {archive_folder}', 'green')
    __clear_folder_contents(folder_path)


def __get_all_file_paths(directory):
    '''
    Remturns a list of all file paths in a given directory
    Except those in the /archive folder
    '''

    # initializing empty file paths list
    file_paths = []

    # crawling through directory and subdirectories
    for root, directories, files in os.walk(directory):
        for filename in files:

            # join the two strings in order to form the full filepath.
            filepath = os.path.join(root, filename)

            # ignore archive folder
            if '/archive' in filepath:
                continue

            file_paths.append(filepath)

    # returning all file paths
    return file_paths


def __clear_folder_contents(folder_path):
    '''
    Clears directory contents
    Ignores: archive, .DS_Store, .gitkeep
    Args:
        folder_path: Path of the folder to clear
    '''

    for subdir in os.listdir(folder_path):
        if subdir not in ('.gitkeep', '.DS_Store', 'archive'):
            subdir_path = f'{folder_path}/{subdir}'
            shutil.rmtree(subdir_path, ignore_errors=False, onerror=None)
