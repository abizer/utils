"""Module for BoD meeting logic."""
import shutil
import textwrap
from datetime import datetime
from math import ceil
from os.path import join

import meetings


def quorum(semester, minutes_filename):
    """Returns the quorum for the given BoD meeting.

    Args:
        semester: the directory name (as given by ``meetings.get_semester()``)
                  for the semester in which the meeting took place
        minutes_filename: the filename of the file containing the minutes for
                          the meeting

    """
    return quorum_next(*meetings.get_prev_meeting('bod', semester,
                                                  datetime.strptime(minutes_filename, '%Y-%m-%d').date()))


def quorum_next(semester, minutes_filename):
    """Returns the quorum for the BoD meeting after the specified one.

    Args:
        semester: the directory name (as given by ``meetings.get_semester()``)
                  for the semester in which the meeting took place
        minutes_filename: the filename of the file containing the minutes for
                          the meeting

    """
    bod_members = ls(semester, minutes_filename)
    if minutes_filename < '2017-11-20':
        return int(ceil(2 / 3 * len(bod_members)))
    else:
        return int(ceil(1 / 2 * len(bod_members)))


def get_bod_minutes_path(semester=meetings.get_semester()):
    """Gets the path to the BoD minutes directory for the given semester."""
    return meetings.get_minutes_path('bod', semester=semester)


def get_attending_directors(semester, minutes_filename):
    """Returns a list of directors present at the given meeting.

    Args:
        semester: the directory name (as given by ``meetings.get_semester()``)
                  for the semester in which the meeting took place
        minutes_filename: the filename of the file containing the minutes for
                          the meeting

    """
    minutes_file = join(get_bod_minutes_path(semester=semester),
                        minutes_filename)
    attendees = []
    with open(minutes_file, 'r') as fin:
        # Skip everything before the line "Directors in attendance:"
        for line in fin:
            if line == 'Directors in attendance:\n':
                break

        for line in fin:
            if line.strip():
                attendees.append(line.strip())
            else:
                break

    assert attendees, 'A BoD meeting needs at least one director present'
    return attendees


def get_attending_guests(semester, minutes_filename):
    """Returns lists of guests present at the given meeting.

    Args:
        semester: the directory name (as given by ``meetings.get_semester()``)
                  for the semester in which the meeting took place
        minutes_filename: the filename of the file containing the minutes for
                          the meeting

    Returns:
        A tuple of two lists. The first list is of guests appointed to BoD at
        that meeting, the second list is of all other guests.

    """
    minutes_file = join(get_bod_minutes_path(semester=semester),
                        minutes_filename)
    joined = []
    visiting = []
    with open(minutes_file, 'r') as fin:
        # Skip everything before the line "Guests in attendance:"
        for line in fin:
            if line == 'Guests in attendance:\n':
                break

        for line in fin:
            line = line.strip()
            if line:
                if line.endswith('*'):
                    joined.append(line[:-1])
                else:
                    visiting.append(line)
            else:
                break

    return (joined, visiting)


def ls(semester, minutes_filename):
    """Lists everyone on BoD at the conclusion of the given meeting.

    Args:
        semester: the directory name (as given by ``meetings.get_semester()``)
                  for the semester in which the meeting took place
        minutes_filename: the filename of the file containing the minutes for
                          the meeting

    Returns:
        A set of BoD members as specified above

    """
    prev_sem, prev_fname = \
        meetings.get_prev_meeting('bod', semester,
                                  datetime.strptime(minutes_filename,
                                                    '%Y-%m-%d').date())

    # FIXME: Always include the GM and SM on this list
    # (And the ASUC EVP and CFO if we want to be pedantic)
    prev_on_bod = set(get_attending_directors(prev_sem, prev_fname)
                      + get_attending_guests(prev_sem, prev_fname)[0])
    cur_on_bod = set(get_attending_directors(semester, minutes_filename)
                     + get_attending_guests(semester, minutes_filename)[0])
    return prev_on_bod | cur_on_bod


def split_attendance(semester, minutes_filename):
    """Splits the attendance section for the given meeting's minutes.

    Splits the attendance section into a section for BoD members, a
    section for guests joining BoD, and a section for guests not joining
    BoD.

    Args:
        minutes_filename: the file containing the minutes for the meeting

    Returns:
        A tuple of two lists. The first list is of guests appointed to BoD at
        that meeting, the second list is of all other guests.

    """
    minutes_file = join(get_bod_minutes_path(semester=semester),
                        minutes_filename)
    with open(minutes_file, 'r') as fin:
        lines = fin.readlines()

    attendance_start = lines.index('Attendance:\n')
    attendance_end = attendance_start + 1
    while (attendance_end < len(lines)
           and lines[attendance_end].strip()):
        attendance_end += 1
    attendees = {l.strip()
                 for l in lines[attendance_start + 1:attendance_end]}

    replacement_lines = []

    replacement_lines.append('Directors in attendance:\n')
    on_bod = set(ls(*meetings.get_prev_meeting('bod', semester,
                                               datetime.strptime(minutes_filename, '%Y-%m-%d').date())))
    for director in sorted(attendees & on_bod):
        replacement_lines.append(director + '\n')
    replacement_lines.append('\n')

    guests = attendees - on_bod
    appointed_guests = []
    visiting_guests = []
    if guests:
        termwidth = shutil.get_terminal_size().columns
        print(textwrap.fill('The following guests are not on BoD. Would they '
                            'like to join, and can they commit to coming '
                            'regularly?', width=termwidth))
        for guest in sorted(guests):
            reply = None
            while reply not in {'y', 'yes', 'n', 'no'}:
                reply = input(guest + ': (y/n) ')
                if reply == 'y' or reply == 'yes':
                    appointed_guests.append(guest)
                else:
                    visiting_guests.append(guest)

    if appointed_guests or visiting_guests:
        replacement_lines.append('Guests in attendance:\n')
        for guest in appointed_guests:
            replacement_lines.append(guest + '*\n')
        for guest in visiting_guests:
            replacement_lines.append(guest + '\n')
        replacement_lines.append('\n')
        replacement_lines.append('Guests marked with a * were appointed to '
                                 'BoD.\n')

    # Replace attendance block in lines with the replacement lines
    lines[attendance_start:attendance_end] = replacement_lines

    with open(minutes_file, 'w') as fout:
        for line in lines:
            fout.write(line)
