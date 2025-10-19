from collections import UserDict
from datetime import datetime
from datetime import timedelta

from pickle import load, dump


class Field:
    """Base class for all fields in a contact record."""

    def __init__(self, value):
        """Initialize a field with a given value."""
        self.value = value

    def __str__(self):
        return str(self.value)

    def __format__(self, format_spec: str) -> str:
        """
        Format the field value according to the format specification.

        Args:
            format_spec (str): Format specification string.

        Returns:
            str: Formatted string representation of the field value.
        """
        return format(str(self.value), format_spec)


class Name(Field):
    """Class representing a contact's name."""

    def __init__(self, value: str):
        """
        Initialize a Name instance.

        Args:
            value (str): The contact's name.

        Raises:
            TypeError: If value is not a string.
            ValueError: If the name is empty.
        """
        if not isinstance(value, str):
            raise TypeError("Name must be a string")
        if not value.strip():
            raise ValueError("Name must not be empty")
        super().__init__(value.strip())

    def __eq__(self, other) -> bool:
        """Compare two Name objects by their value."""
        return isinstance(other, Name) and self.value == other.value


class Phone(Field):
    """Class representing a phone number."""

    def __init__(self, value: str):
        """
        Initialize a Phone instance with validation.

        Args:
            value (str): The phone number (must contain exactly 10 digits).

        Raises:
            TypeError: If value is not a string.
            ValueError: If the phone number does not consist of 10 digits.
        """
        if not isinstance(value, str):
            raise TypeError("Phone number must be a string")
        if not value.isdigit() or len(value) != 10:
            raise ValueError("Phone number must contain exactly 10 digits")
        super().__init__(value)

    def __eq__(self, other) -> bool:
        """Compare two Phone objects by their value."""
        return isinstance(other, Phone) and self.value == other.value


class Birthday(Field):
    """Class representing a birthday date."""

    def __init__(self, value: str | datetime):
        """
        Initialize a Birthday instance.

        Args:
            value (str | datetime): Birthday date as string in 'DD.MM.YYYY' format or datetime object.

        Raises:
            TypeError: If value is neither a string nor a datetime object.
            ValueError: If the date string format is invalid.
        """

        if isinstance(value, datetime):
            self.value = value
            return

        if not isinstance(value, str):
            raise TypeError(
                "Birthday number must be a string in 'DD.MM.YYYY' format or datetime"
            )

        try:
            self.value = datetime.strptime(value, "%d.%m.%Y")
        except ValueError as e:
            raise ValueError("Invalid date format. Use DD.MM.YYYY") from e


class Record:
    """Class representing a single contact record."""

    def __init__(self, name: str):
        """
        Initialize a record with a name and optional list of phone numbers.

        Args:
            name (str): The contact's name.

        Raises:
            ValueError: If the name is invalid.
        """
        self.name: Name = Name(name)
        self.phones: list[Phone] = []
        self.birthday: Birthday | None = None

    def add_birthday(self, bday: str | Birthday) -> None:
        """
        Add a birthday to the contact.

        Args:
            bday (str | Birthday): Birthday as string in 'DD.MM.YYYY' format or Birthday object.

        Raises:
            ValueError: If birthday already exists for this contact.
        """
        if self.birthday:
            raise ValueError("Birthday already exists")

        self.birthday = Birthday(bday)

    def add_phone(self, phone: str) -> None:
        """
        Add a new phone number to the contact.

        Args:
            phone (str): Phone number to add.

        Raises:
            ValueError: If the phone is invalid or already exists.
        """
        new_phone = Phone(phone)
        if new_phone in self.phones:
            raise ValueError("Phone already exists")
        self.phones.append(new_phone)

    def remove_phone(self, phone: str) -> None:
        """
        Remove a phone number from the contact.

        Args:
            phone (str): Phone number to remove.

        Raises:
            ValueError: If the phone is not found.
        """
        try:
            self.phones.remove(Phone(phone))
        except ValueError:
            raise ValueError("Phone not found")

    def edit_phone(self, old_phone: str, new_phone: str) -> None:
        """
        Edit an existing phone number.

        Args:
            old_phone (str): The phone number to replace.
            new_phone (str): The new phone number.

        Raises:
            ValueError: If the old phone does not exist or new one is invalid.
        """
        if Phone(new_phone) in self.phones:
            raise ValueError("New phone already exists")

        try:
            index = self.phones.index(Phone(old_phone))
            self.phones[index] = Phone(new_phone)
        except ValueError:
            raise ValueError(f"Phone '{old_phone}' not found")

    def find_phone(self, phone: str) -> Phone | None:
        """
        Find a phone number in the contact.

        Args:
            phone (str): Phone number to find.

        Returns:
            Phone | None: Found Phone object or None if not found.
        """
        for p in self.phones:
            if p.value == phone:
                return p
        return None

    def __str__(self):
        phones_str = "; ".join(p.value for p in self.phones) or "No phones"
        return f"Contact name: {self.name.value}, phones: {phones_str}"


class AddressBook(UserDict):
    """Class representing an address book for managing contact records."""

    def add_record(self, record: Record) -> None:
        """
        Add a new record to the address book.

        Args:
            record (Record): The contact record to add.

        Raises:
            TypeError: If record is not a Record instance.
            ValueError: If a record with the same name already exists.
        """
        if not isinstance(record, Record):
            raise TypeError("Argument must be a Record instance")
        if record.name.value in self.data:
            raise ValueError(f"Record with name '{record.name.value}' already exists")
        self.data[record.name.value] = record

    def find(self, name: str) -> Record | None:
        """
        Find a contact record by name.

        Args:
            name (str): Contact name.

        Returns:
            Record | None: Found record or None if not found.
        """
        return self.data.get(name)

    def delete(self, name: str) -> None:
        """
        Delete a contact record by name.

        Args:
            name (str): Contact name to delete.

        Raises:
            KeyError: If the contact does not exist.
        """
        if name not in self.data:
            raise KeyError(f"Contact '{name}' not found")
        del self.data[name]

    def get_upcoming_birthdays(self) -> list[dict[str:Record]]:
        """
        Get list of contacts with birthdays in the next 7 days.

        If a birthday falls on a weekend (Saturday or Sunday), the congratulation
        date is moved to the next Monday.

        Returns:
            list[dict]: List of dictionaries with 'name' and 'congratulation_date' keys.
                       Empty list if no upcoming birthdays or no contacts.
        """
        if not len(self.data):
            return []

        today = datetime.today().date()

        bdays: list[datetime | None] = [
            record.birthday.value.date().replace(year=today.year)
            for record in self.data.values()
        ]

        congrat_dates = [
            (
                bday
                if (bday - today) >= timedelta(days=0)
                and (bday - today) <= timedelta(days=7)
                else None
            )
            for bday in bdays
        ]

        SATURDAY = 5
        congrat_dates = [
            (
                date + timedelta(days=7 - date.weekday())
                if date and date.weekday() >= SATURDAY
                else date
            )
            for date in congrat_dates
        ]

        ret = []
        for username, date in zip(self.data.keys(), congrat_dates):
            if date:
                ret.append(
                    {
                        "name": username,
                        "congratulation_date": date.strftime("%Y.%m.%d"),
                    }
                )

        return ret

    def __iter__(self):
        return super().__iter__()


class AddressBookStorage:
    """Class responsible for saving and loading AddressBook data."""

    def __init__(self, filename="addressbook.pkl"):
        """
        Initialize storage with filename.

        Args:
            filename (str): Path to the storage file.
        """
        self.filename = filename

    def save(self, book: AddressBook) -> None:
        """
        Save address book to file using pickle.

        Args:
            book (AddressBook): Address book instance to save.
        """
        with open(self.filename, "wb") as f:
            dump(book, f)

    def load(self) -> AddressBook:
        """
        Load address book from file using pickle.

        Returns:
            AddressBook: Loaded address book or new empty one if file not found.
        """
        try:
            with open(self.filename, "rb") as f:
                return load(f)
        except FileNotFoundError:
            return AddressBook()  # Return new empty address book


# Tests


def make_record(name: str, phones=None, birthday=""):
    rec = Record(name)

    if phones is None:
        phones = []

    for phone in phones:
        rec.add_phone(phone)
    if birthday:
        rec.add_birthday(birthday)
    return rec


def main():
    storage = AddressBookStorage()
    book = storage.load()

    for key in book:
        print(book[key])
    try:
        book.add_record(make_record("Jack", ["5554446464"], "05.10.2001"))
        book.add_record(make_record("John", ["1234567890", "5555555555"], "14.10.2004"))
        book.add_record(make_record("Roman", ["3334445566"], "20.09.2000"))
    except ValueError:
        print("Users already exist")

    storage.save(book)
    print("\nData saved successfully!")


if __name__ == "__main__":
    main()
