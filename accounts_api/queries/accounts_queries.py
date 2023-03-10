from pydantic import BaseModel
from typing import Optional, List, Union
from queries.pool import pool
from fastapi import HTTPException, status
import psycopg


class DuplicateAccountError(ValueError):
    pass


class Error(BaseModel):
    message: str


class AccountIn(BaseModel):
    username: str
    name: str
    is_chef: bool
    pay_rate: Optional[str]
    cuisine: Optional[str]
    years_of_experience: Optional[int]
    picture_url: Optional[str]


class AccountInWithPassword(AccountIn):
    password: str


class AccountOut(BaseModel):
    id: int
    username: str
    name: str
    is_chef: bool
    pay_rate: Optional[str]
    cuisine: Optional[str]
    years_of_experience: Optional[int]
    picture_url: Optional[str]
    events_favorited: Optional[list[int]]


class AccountOutWithPassword(AccountOut):
    password: str


class FavoriteIn(BaseModel):
    event_id: int


class FavoriteListOut(BaseModel):
    events_favorited: list[int]


class AccountRepository:
    def create(
        self,
        account: AccountInWithPassword,
        hashed_password: str
    ):
        with pool.connection() as connection:
            with connection.cursor() as db:
                try:
                    result = db.execute(
                        """
                        INSERT INTO accounts
                            (username, password, name, is_chef, pay_rate,
                            cuisine, years_of_experience, picture_url)
                        VALUES
                            (%s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id;
                        """,
                        [
                            account.username,
                            hashed_password,
                            account.name,
                            account.is_chef,
                            account.pay_rate,
                            account.cuisine,
                            account.years_of_experience,
                            account.picture_url,
                        ],
                    )
                    id = result.fetchone()[0]
                    old_data = account.dict()

                    return AccountOutWithPassword(id=id, **old_data)
                except psycopg.OperationalError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Error inserting data into database",
                    )
                except psycopg.errors.UniqueViolation:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Account already exists",
                    )

    def get(self, username: str) -> AccountOutWithPassword:
        with pool.connection() as connection:
            with connection.cursor() as db:
                result = db.execute(
                    """
                    SELECT (id, username, name, is_chef, pay_rate, cuisine,
                            years_of_experience, picture_url, password)
                    FROM accounts
                    WHERE username=(%s);
                    """,
                    [username],
                )
                row = result.fetchone()[0]
        if not result:
            return None
        return AccountOutWithPassword(
            id=row[0],
            username=row[1],
            name=row[2],
            is_chef=row[3],
            pay_rate=row[4],
            cuisine=row[5],
            years_of_experience=row[6],
            picture_url=row[7],
            password=row[8]
        )

    def update(self, form_data: AccountIn, user_id: int) -> AccountOut:
        with pool.connection() as connection:
            with connection.cursor() as db:
                db.execute(
                    """
                    UPDATE accounts
                    SET username = %s,
                        name = %s,
                        is_chef = %s,
                        pay_rate = %s,
                        cuisine = %s,
                        years_of_experience = %s,
                        picture_url = %s
                    WHERE id = %s;
                    """,
                    [
                        form_data.username,
                        form_data.name,
                        form_data.is_chef,
                        form_data.pay_rate,
                        form_data.cuisine,
                        form_data.years_of_experience,
                        form_data.picture_url,
                        user_id
                    ]
                )
                old_data = form_data.dict()
                return AccountOut(id=user_id, **old_data)

    def get_all(self) -> Union[Error, List[AccountOut]]:
        try:
            with pool.connection() as conn:
                with conn.cursor() as db:
                    result = db.execute(
                        """
                        SELECT id, username, name, is_chef, pay_rate,
                        cuisine, years_of_experience, picture_url
                        FROM accounts
                        ORDER BY name;
                        """
                    )
                    result = []
                    for record in db:
                        Account = AccountOut(
                            id=record[0],
                            username=record[1],
                            name=record[2],
                            is_chef=record[3],
                            pay_rate=record[4],
                            cuisine=record[5],
                            years_of_experience=record[6],
                            picture_url=record[7],
                        )
                        result.append(Account)
                    return result
        except Exception as e:
            print(e)
            return {"message": "Could not get all accounts"}

    def favorite(self, event: FavoriteIn, user_id: int):
        with pool.connection() as connection:
            with connection.cursor() as db:
                result = db.execute(
                    """
                    SELECT events_favorited
                    FROM accounts
                    WHERE id = %s;
                    """,
                    [user_id]
                )
                for row in result:
                    event_list = row[0]
                    if event_list is None or event.event_id not in event_list:
                        result = db.execute(
                            """
                            UPDATE accounts
                            SET events_favorited
                                = array_append(events_favorited, %s)
                            WHERE id = %s
                            RETURNING accounts.events_favorited;
                            """,
                            [event.event_id, user_id]
                        )
                    else:
                        result = db.execute(
                            """
                            UPDATE accounts
                            SET events_favorited
                                = array_remove(events_favorited, %s)
                            WHERE id = %s
                            RETURNING accounts.events_favorited;
                            """,
                            [event.event_id, user_id]
                        )
                    events = result.fetchone()[0]
                    return FavoriteListOut(events_favorited=events)

    def get_detail(self, user_id: int) -> Union[Error, AccountOut]:
        try:
            with pool.connection() as conn:
                with conn.cursor() as db:
                    result = db.execute(
                        """
                        SELECT id,
                        username,
                        name,
                        is_chef,
                        pay_rate,
                        cuisine,
                        years_of_experience,
                        picture_url
                        FROM accounts
                        WHERE id = %s;
                        """,
                        [user_id]
                    )
                    chef = result.fetchone()
                    Account = AccountOut(
                        id=chef[0],
                        username=chef[1],
                        name=chef[2],
                        is_chef=chef[3],
                        pay_rate=chef[4],
                        cuisine=chef[5],
                        years_of_experience=chef[6],
                        picture_url=chef[7],
                    )
                    return Account
        except Exception as e:
            print(e)
            return {"message": "No such chef exist"}
