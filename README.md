# Birthday Reminder – Coursework Report

**Author:** Grigas
**Course:** Object‑Oriented Programming – Coursework 2025  
**Repository:** <https://github.com/TwiceAdopted/Kursinisdarbas25/blob/main/kursinis.py>  
**Date:** 2025‑05‑04

## 1  Introduction

### 1.1 Goal of the coursework  
Create a python code that can save birthdays, track them, notify the user fo an upcoming birthday. The code is to meet all the criteria in the provided PDF.

### 1.2 How to run the program  

python3 kursinis.py --help       # usage guide
python3 kursinis.py --test       # run unit‑tests


### 1.3 How to use the program (quick demo)  

python3 kursinis.py add    --user alice --name Bob --day 24 --month 1
python3 kursinis.py list   --user alice
python3 kursinis.py remind --user alice --channel console


## 2  Analysis

| Requirement | Implementation | Code reference |
|-------------|----------------|----------------|
| 4 OOP pillars | Encapsulation (User._birthdays), Abstraction (Notifier ABC), Inheritance (ConsoleNotifier / EmailNotifier), Polymorphism (notifier.send(...)) | Lines 60‑78, 115‑124, 127‑155, 230‑233 |
| Design pattern | Factory‑Method (`NotifierFactory.create`) + Singleton (`_Storage`) | Lines 160‑180, 90‑110 |
| Composition | `User` *has‑a* list of `Birthday`s | Line 60 (`self._birthdays`) |
| File IO | `_Storage._load()` / `_save()` JSON to `~/.birthday_reminder.json` | Lines 100‑110 |
| Unit tests | `_TestBirthdayReminder` (6 passing tests) | Lines 240‑310 |
| CLI functions | `add`, `remove`, `list`, `remind` (argparse sub‑commands) | Lines 190‑233 |  (Command line interface)
| PEP 8 style | Passes `ruff` / `flake8` with 0 warnings | `ruff check birthday_reminder.py` |


Encapsulation - grouping data into one unit (class) and restricting accses to the internals from the outside. 
Ie. An ATM allows you to deposit or withdraw money, but wont let you see how much money is actually in the ATM. 

Abstraction - Shows only the operations an object needs to expose, while hiding the complex code to make it more appealing. 
Ie. When you press the Volume button on your TV remote, you have no idea that the infrared LED needs to colaborate with parts of the TV, and you dont need to.

Inheritance - allows a sub-class to inherit a trait from the super-class.
Ie. We inherit our hair colour from our parents.

Polymorphism - one interface, many interchangable implementations.
When creating your character in a video game, you can choose betwen many options fo clothes, hair, accessories, etc.

Factory method - a way to create objects without doing the same thing every time. When a new class appears, you dont 
want to re-write the entire code.
Ie. You (client) ask the barista (factory) for a espresso. The barista decides what machine and recipie 
to use, hands you a drink that satisfies the coffee requirments. Next day they add a new coffee, but the only
change is in the baristas recipe switch, not the clients phrasing.

Singleton design pattern - guarantees that a class has only one instance and gives a global access
point to it.
Ie. At the airport, all the planes must comminucate with one controll tower, to safelly land. Global 
access point would be a radio frequency that all the planes use to contact the tower.





## 3  Results

* Application runs on Python 3.7‑3.12 and passes all tests.  
* All coursework requirements met, verified by manual review.
* Learned practical use of Factory‑Method & Singleton patterns. Hardedst part was setting up github, understanding how and when the terminal works, where to direct it.
* The code obviusly had lots of errors, but nothing a little time invested cant fix, wathced lots of youtube videos, asked for lots of help. :) 

## 4  Conclusions

The project demonstrates a clean, extensible design. Future extensions could include a real e-mail notification or sms.

---

## References

* Python PEP 8 – Style Guide for Python Code  
* Python `unittest` documentation  
* *Design Patterns: Elements of Reusable Object‑Oriented Software*  
* Real Python – Factory Method & Singleton in Python  
