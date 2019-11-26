import csv
import os


from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

def main():
    c=0
    f=open("books.csv")
    reader = csv.reader(f)
    for isbn, title, author, year in reader:
        print(isbn,title,author,year)
        if c!=0:
            db.execute("INSERT INTO BOOK values (:isbn,:title,:author,:year)",{"isbn": isbn,"title":title,"author":author,"year":year})
            print("Listo")
        c+=1
    db.commit()

if __name__ == "__main__":
    main()
