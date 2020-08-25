import sys
from termcolor import cprint

import pandas as pd
from pandas.errors import EmptyDataError, ParserError


def load_specifications(path):
    """TODO docstring
    """
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
                     'Body', 'Watermark', 'Watermark Position'}

    actual_cols = set(list(specs))

    # Check that we have all the columns we expect
    if expected_cols != actual_cols:
        cprint('\nERROR: Missing or incorrect columns in specs.csv', 'red')
        cprint(f'Expected columns: {expected_cols}\n')
        sys.exit()

    return specs


def get_video_attributes(row):
    """TODO
    """

    course = row['Course'] if has_value(row['Course']) else None
    section = row['Section'] if has_value(row['Section']) else None
    instructor = row['Instructor'] if has_value(row['Instructor']) else None
    title = row['Title'] if has_value(row['Title']) else None
    top_slate = row['Top Slate'] if has_value(row['Top Slate']) else None
    body = row['Body'] if has_value(row['Body']) else None
    watermark = row['Watermark'] if has_value(row['Watermark']) else None
    wm_pos = row['Watermark Position'] if has_value(
        row['Watermark Position']) else None

    all_vals = [course, section, instructor, title,
                top_slate, body, watermark, wm_pos]

    vals = filter((lambda v: v is not None), all_vals)

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

    # all fields must not contain invalid characters
    if all(map(_has_invalid_char, vals)):
        cprint('\nERROR: Contains illegal character', 'red')
        raise ValueError()

    # if top slate is specified must finish with mp4
    if top_slate is not None and str(top_slate)[-4:] != '.mp4':
        cprint('\nERROR: Must include value for slate that ends in .mp4', 'red')
        raise ValueError()

    if len(title) > 45:
        cprint('\nERROR: Does not support titles with more than 45 characters', 'red')
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
        'wm_pos': wm_pos
    }


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


def _has_invalid_char(str_val):

    invalid_chars = ['/', '|', '@', '^']

    for char in invalid_chars:
        if str_val.find(char) != -1:
            print(f'FAILED: {str_val}')
            return True

    return False
