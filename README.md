# RC522-Attendance

The program creates a new log file every Monday, which can be found in the `logs` folder.  
The format of the log file is `csv`, so it can easily be imported to Microsoft Excel.

## Program usage

- First you have to register the cards in the system. Run the command below, hover the card on the scanner, and the program will ask you to enter the name of the owner of that card. Once you enter a name, you will be given two choices. You can either type "yes" to continue registering cards, or you can type "no" to exit the program.

```python
python3 register_cards.py
```

- If you've done registering the cards, now you can run the main program to start logging with the command below.

```python
python3 read_cards.py
```
