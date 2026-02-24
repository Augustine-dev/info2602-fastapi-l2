import typer
from app.database import create_db_and_tables, get_session, drop_all
from app.models import User, Todo, TodoCategory, Category
from fastapi import Depends
from sqlmodel import select
from sqlalchemy.exc import IntegrityError

cli = typer.Typer()

@cli.command()
def initialize():
    with get_session() as db: # Get a connection to the database
        drop_all() # delete all tables
        create_db_and_tables() #recreate all tables
        bob = User('bob', 'bob@mail.com', 'bobpass') # Create a new user (in memory)
        db.add(bob) # Tell the database about this new data
        db.commit() # Tell the database persist the data
        db.refresh(bob) # Update the user (we use this to get the ID from the db)
        print("Database Initialized")

@cli.command()
def get_user(username:str):
    # The code for task 5.1 goes here. Once implemented, remove the line below that says "pass"
    with get_session() as db: # Get a connection to the database
        user = db.exec(select(User).where(User.username == username)).first()
        if not user:
            print(f'{username} not found!')
            return
        print(user)

@cli.command()
def get_all_users():
    # The code for task 5.2 goes here. Once implemented, remove the line below that says "pass"
    with get_session() as db:
        all_users = db.exec(select(User)).all()
        if not all_users:
            print("No users found")
        else:
            for user in all_users:
                print(user)


@cli.command()
def change_email(username: str = typer.Argument(..., help="The new username")
                 , new_email:str = typer.Argument(..., help="The new email")):
    # The code for task 6 goes here. Once implemented, remove the line below that says "pass"
    with get_session() as db: # Get a connection to the database
        user = db.exec(select(User).where(User.username == username)).first()
        if not user:
            print(f'{username} not found! Unable to update email.')
            return
        user.email = new_email
        db.add(user)
        db.commit()
        print(f"Updated {user.username}'s email to {user.email}")

@cli.command()
def create_user(username: str = typer.Argument(..., help="The username for the new user")
                , email:str = typer.Argument(..., help="The email for the new user")
                , password: str = typer.Argument(..., help="The password for the new user")):
    # The code for task 7 goes here. Once implemented, remove the line below that says "pass"
    with get_session() as db: # Get a connection to the database
        newuser = User(username, email, password)
        try:
            db.add(newuser)
            db.commit()
        except IntegrityError as e:
            db.rollback() #let the database undo any previous steps of a transaction
            #print(e.orig) #optionally print the error raised by the database
            print("Username or email already taken!") #give the user a useful message
        else:
            print(newuser) # print the newly created user

@cli.command()
def delete_user(username: str = typer.Argument(..., help="The username to be deleted")):
    # The code for task 8 goes here. Once implemented, remove the line below that says "pass"
    with get_session() as db:
        user = db.exec(select(User).where(User.username == username)).first()
        if not user:
            print(f'{username} not found! Unable to delete user.')
            return
        db.delete(user)
        db.commit()
        print(f'{username} deleted')

@cli.command()
def add_task(username:str, task:str):
    with get_session() as db:
        user = db.exec(select(User).where(User.username == username)).one_or_none()
        if not user:
            print("User doesn't exist")
            return
        user.todos.append(Todo(text=task))
        db.add(user)
        db.commit()
        print("Task added for user")

@cli.command()
def toggle_todo(todo_id:int, username:str):
    with get_session() as db:
        todo = db.exec(select(Todo).where(Todo.id == todo_id)).one_or_none()
        if not todo:
            print("This todo doesn't exist")
            return
        if todo.user.username != username:
            print(f"This todo doesn't belong to {username}")
            return

        todo.toggle()
        db.add(todo)
        db.commit()

        print(f"Todo item's done state set to {todo.done}")

@cli.command()
def list_todo_categories(todo_id:int, username:str):
    with get_session() as db: # Get a connection to the database
        todo = db.exec(select(Todo).where(Todo.id == todo_id)).one_or_none()
        if not todo:
            print("Todo doesn't exist")
        elif not todo.user.username == username:
            print("Todo doesn't belong to that user")
        else:
            print(f"Categories: {todo.categories}")

@cli.command()
def create_category(username:str, cat_text:str):
    with get_session() as db: # Get a connection to the database
        user = db.exec(select(User).where(User.username == username)).one_or_none()
        if not user:
            print("User doesn't exist")
            return

        category = db.exec(select(Category).where(Category.text== cat_text, Category.user_id == user.id)).one_or_none()
        if category:
            print("Category exists! Skipping creation")
            return
        
        category = Category(text=cat_text, user_id=user.id)
        db.add(category)
        db.commit()

        print("Category added for user")

@cli.command()
def list_user_categories(username:str):
    with get_session() as db: # Get a connection to the database
        user = db.exec(select(User).where(User.username == username)).one_or_none()
        if not user:
            print("User doesn't exist")
            return
        categories = db.exec(select(Category).where(Category.user_id == user.id)).all()
        print([category.text for category in categories])

@cli.command()
def assign_category_to_todo(username:str, todo_id:int, category_text:str):
    with get_session() as db: # Get a connection to the database
        user = db.exec(select(User).where(User.username == username)).one_or_none()
        if not user:
            print("User doesn't exist")
            return
        
        category = db.exec(select(Category).where(Category.text == category_text, Category.user_id==user.id)).one_or_none()
        if not category:
            category = Category(text=category_text, user_id=user.id)
            db.add(category)
            db.commit()
            print("Category didn't exist for user, creating it")
        
        todo = db.exec(select(Todo).where(Todo.id == todo_id, Todo.user_id==user.id)).one_or_none()
        if not todo:
            print("Todo doesn't exist for user")
            return
        
        todo.categories.append(category)
        db.add(todo)
        db.commit()
        print("Added category to todo")

#Exercise 1 Lab 2
@cli.command()
def search_string(query: str = typer.Argument(..., help="The inputted query to search the database")):
    with get_session() as db:
        searcher = db.exec(select(User).where(User.username.contains(query) | (User.email.contains(query)))).all() 
        if not searcher:
            print(f'No users found with "{query}" in username or email!')
        else:
            for user in searcher:
                print(user)

#Exercise 2 Lab 2
@cli.command()
def get_n_users(limit: int = typer.Argument(10, help="How many users to show"),
                offset: int = typer.Argument(0, help="How many to skip")):
    with get_session() as db:
        user_list = db.exec(select(User).offset(offset).limit(limit)).all()
        if not user_list:
            print("No users found!")
        else:
            for user in user_list:
                print(user)

#Exercise 3 Lab 2

#Exercise 1 Lab 3
@cli.command()
def list_todos():
    with get_session() as db:
        lister = db.exec(select(Todo)).all()
        if not lister:
            print("No todos found!")
        else:
            for todo in lister:
                print(f"ID: {todo.id}, Text: {todo.text}, Username: {todo.user.username}, Status: {'Done' if todo.done else 'Not Done'}")

#Exercise 2 Lab 3
@cli.command()
def delete_todo(todo_id: int = typer.Argument(..., help="The ID of the todo to delete")):
    with get_session() as db:
        todo = db.exec(select(Todo).where(Todo.id == todo_id)).one_or_none()
        if not todo:
            print("Todo not found!")
            return
        db.delete(todo)
        db.commit()
        print("Todo deleted")

#Exercise 3 Lab 3
@cli.command()
def complete_toggle_all(username: str = typer.Argument(..., help="The username whose todos you want to toggle")):
    with get_session() as db:
        user = db.exec(select(User).where(User.username == username)).one_or_none()
        if not user:
            print("User not found!")
            return
        for todo in user.todos:
            todo.done = True
            db.add(todo)
        db.commit()
        print(f"Toggled all todos for {username}")

if __name__ == "__main__":
    cli()