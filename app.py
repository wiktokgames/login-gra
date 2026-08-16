from flask import Flask, render_template, request, redirect, session, jsonify
import psycopg2
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "supertajne"


def polacz_z_baza():
    return psycopg2.connect(os.environ["DATABASE_URL"])
 
# stworzenie tabel raz, na starcie
polaczenie_startowe = polacz_z_baza()
polaczenie_startowe.cursor().execute(
    "CREATE TABLE IF NOT EXISTS users (id SERIAL PRIMARY KEY, login TEXT, haslo TEXT)"
)
polaczenie_startowe.cursor().execute(
    "CREATE TABLE IF NOT EXISTS wyniki (id SERIAL PRIMARY KEY, user_id INTEGER, wartosc INTEGER)"
)
polaczenie_startowe.cursor().execute(
    "ALTER TABLE wyniki ADD COLUMN IF NOT EXISTS mnoznik INTEGER DEFAULT 1"
)
polaczenie_startowe.commit()
polaczenie_startowe.close()


@app.route("/")
def strona_glowna():
    return redirect("/menu")


@app.route("/menu")
def menu():
    czy_zalogowany = "login" in session
    return render_template("menu.html", zalogowany=czy_zalogowany)


@app.route("/ranking")
def ranking():
    polaczenie = polacz_z_baza()
    cursor = polaczenie.cursor()

    # TODO 1: wykonaj zapytanie JOIN pokazane wyżej
    cursor.execute("SELECT users.login, wyniki.wartosc FROM wyniki JOIN users ON wyniki.user_id = users.id ORDER BY wyniki.wartosc DESC")

    # TODO 2: pobierz WSZYSTKIE wyniki (fetchall, nie fetchone - chcemy całą listę)
    wyniki_lista = cursor.fetchall()

    polaczenie.close()

    return render_template("ranking.html", wyniki=wyniki_lista)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        login_wpisany = request.form["login"]
        haslo_wpisane = request.form["haslo"]

        polaczenie = polacz_z_baza()
        cursor = polaczenie.cursor()

        cursor.execute("SELECT id, haslo FROM users WHERE login = %s", (login_wpisany,))
        wynik = cursor.fetchone()
        polaczenie.close()

        if wynik and check_password_hash(wynik[1], haslo_wpisane):
            session["login"] = login_wpisany
            session["user_id"] = wynik[0]
            return redirect("/gra")
        else:
            return "Złe hasło lub login nie istnieje"

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        login_wpisany = request.form["login"]
        haslo_wpisane = request.form["haslo"]
        haslo_hash = generate_password_hash(haslo_wpisane)

        polaczenie = polacz_z_baza()
        cursor = polaczenie.cursor()
        cursor.execute("INSERT INTO users (login, haslo) VALUES (%s, %s)", (login_wpisany, haslo_hash))
        polaczenie.commit()
        polaczenie.close()

        return redirect("/login")

    return render_template("register.html")


@app.route("/gra")
def gra():
    if "login" not in session:
        return redirect("/login")

    user_id = session["user_id"]
    polaczenie = polacz_z_baza()
    cursor = polaczenie.cursor()
    cursor.execute("SELECT wartosc FROM wyniki WHERE user_id = %s", (user_id,))
    wynik = cursor.fetchone()
    polaczenie.close()

    aktualna_wartosc = wynik[0] if wynik else 0

    return render_template("gra.html", wartosc=aktualna_wartosc)

@app.route("/sklep")
def sklep():
    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]
    polaczenie = polacz_z_baza()
    cursor = polaczenie.cursor()

    cursor.execute("SELECT wartosc, mnoznik FROM wyniki WHERE user_id = %s", (user_id,))
    wynik = cursor.fetchone()
    polaczenie.close()

    if wynik is None:
        punkty, mnoznik = 0, 1
    else:
        punkty, mnoznik = wynik

    koszt = mnoznik * 10

    return render_template("sklep.html", punkty=punkty, mnoznik=mnoznik, koszt=koszt)



@app.route("/kup_ulepszenie")
def kup_ulepszenie():
    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]
    polaczenie = polacz_z_baza()
    cursor = polaczenie.cursor()

    # TODO 1: pobierz aktualne "wartosc" i "mnoznik" dla tego usera
    # (dokładnie ten sam wzorzec co w sklep() i zwieksz_wynik())
    cursor.execute("SELECT wartosc, mnoznik FROM wyniki WHERE user_id = %s", (user_id,))
    wynik = cursor.fetchone()

    if wynik is None:
        polaczenie.close()
        return jsonify(sukces=False, powod="Brak wyniku")

    # TODO 2: rozpakuj wynik na "wartosc" i "mnoznik"
    wartosc, mnoznik = wynik

    koszt = mnoznik * 10

    if wartosc >= koszt:
        # TODO 3: oblicz nową wartość (wartosc - koszt) i nowy mnożnik (mnoznik + 1)
        nowy_mnoznik = mnoznik + 1
        nowa_wartosc = wartosc - koszt

        # TODO 4: zaktualizuj oba pola naraz w bazie
        # UPDATE wyniki SET wartosc = %s, mnoznik = %s WHERE user_id = %s
        cursor.execute("UPDATE wyniki SET wartosc = %s, mnoznik = %s WHERE user_id = %s", (nowa_wartosc, nowy_mnoznik, user_id))
        polaczenie.commit()
        polaczenie.close()

        return jsonify(sukces=True, wartosc=nowa_wartosc, mnoznik=nowy_mnoznik, koszt=nowy_mnoznik * 10)
    else:
        polaczenie.close()
        return jsonify(sukces=False, powod="Za mało punktów")




@app.route("/zwieksz_wynik")
def zwieksz_wynik():
    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]
    polaczenie = polacz_z_baza()
    cursor = polaczenie.cursor()

    # TODO 1: pobierz teraz DWIE kolumny: "wartosc" i "mnoznik"
    # (spójrz jak to zrobiłeś w funkcji sklep() - ten sam wzorzec)
    cursor.execute("SELECT wartosc, mnoznik FROM wyniki WHERE user_id = %s", (user_id,))
    wynik = cursor.fetchone()

    if wynik is None:
        cursor.execute("INSERT INTO wyniki (user_id, wartosc) VALUES (%s, %s)", (user_id, 1))
        nowa_wartosc = 1
    else:
        # TODO 2: rozpakuj "wynik" na dwie zmienne: wartosc i mnoznik
        # (spójrz jak to zrobiłeś w sklep(): "punkty, mnoznik = wynik")
        wartosc, mnoznik = wynik
        # TODO 3: nowa_wartosc to stara wartosc + mnoznik (zamiast zawsze + 1)
        nowa_wartosc = wartosc + mnoznik

        cursor.execute("UPDATE wyniki SET wartosc = %s WHERE user_id = %s", (nowa_wartosc, user_id))

    polaczenie.commit()
    polaczenie.close()

    return jsonify(wartosc=nowa_wartosc)


@app.route("/logout")
def logout():
    # TODO: wyczyść sesję (session.clear())
    session.clear()
    return redirect("/menu")


if __name__ == "__main__":
    app.run(debug=True)