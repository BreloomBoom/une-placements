# une-placements

A simple script which assigns clinical schools to students based on their preferences and availabilities.

# Adding Schools

Add a text file in csv format where the ____ column is ____
- First: School Name
- Second: Capacity for the School

# Adding Students
Add a text file in csv format where the ____ column is ____

- First: Student Name
- Second: Ranking for the First School
- Third: Ranking for the Second School
- Fourth: Ranking for the Third School
and so on...

The order of schools will match the order in the school file.

# Using the program

## Install the Packages

```pip install -r requirements.txt```

## Run the Program

```python3 placements.py [schools file] [students file]```

e.g.

```python3 placements.py schools_ex.csv students_ex.csv```