class DISCORD:
    """"
    Main Discord configuration class.
    """
    TOKEN: str = "MTI4NDAzNzAyNjY3MjI3OTYzNQ.G0a27l.oRGTR-khPGuPmjVugjJncCkN8z3sa3p4BBNZ18"
    PREFIX: str = ","
    APPLICATION_ID: int = 1305237030200147968
    CLIENT_ID: int = 1305237030200147968
    PUBLIC_KEY: str = "3c81f24f1d25e679241eedfcd1d93be1a31e2479e680a49253b6e4a6c39f8e46"
    OWNER_IDS: list[int] = [
        785042666475225109,
        598125772754124823,
        1332327503062106154,
        608450597347262472,
        1268333988376739931,
        1250897828256153670,
        1342432632444813345
    ]
    VANITY_TOKEN: str = "MTI5NjIwNzM1NTk0MzQ1Mjc2NA.G4WbwX.SqBBKn0vCqLBXekufXFljmR8UvOTxqWnmL6XUc"

class VANITY:
    VANITY_TOKEN: str = "MTI5NjIwNzM1NTk0MzQ1Mjc2NA.G4WbwX.SqBBKn0vCqLBXekufXFljmR8UvOTxqWnmL6XUc"
    PREFIX: str = "v!"
    OWNER_IDS: list[int] = [
        785042666475225109,
        598125772754124823,
        608450597347262472,
        1268333988376739931
    ]

class DATABASE:
    """
    Postgres authentication class.
    """
    DSN: str = "postgres://postgres:admin@localhost/hersey"