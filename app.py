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
polaczenie_startowe.commit()
polaczenie_startowe.close()


@app.route("/")
def strona_glowna():
    return redirect("/menu")


@app.route("/menu")
def menu():
    czy_zalogowany = "login" in session
    return render_template("menu.html", zalogowany=czy_zalogowany)


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


@app.route("/zwieksz_wynik")
def zwieksz_wynik():
    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]
    polaczenie = polacz_z_baza()
    cursor = polaczenie.cursor()

    cursor.execute("SELECT wartosc FROM wyniki WHERE user_id = %s", (user_id,))
    wynik = cursor.fetchone()

    if wynik is None:
        cursor.execute("INSERT INTO wyniki (user_id, wartosc) VALUES (%s, %s)", (user_id, 1))
        nowa_wartosc = 1
    else:
        nowa_wartosc = wynik[0] + 1
        cursor.execute("UPDATE wyniki SET wartosc = %s WHERE user_id = %s", (nowa_wartosc, user_id))

    polaczenie.commit()
    polaczenie.close()

    return jsonify(wartosc=nowa_wartosc)


@app.route("/reset_wynik")
def reset_wynik():
    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]
    polaczenie = polacz_z_baza()
    cursor = polaczenie.cursor()

    cursor.execute("UPDATE wyniki SET wartosc = %s WHERE user_id = %s", (0, user_id))

    polaczenie.commit()
    polaczenie.close()

    return jsonify(wartosc=0)


@app.route("/logout")
def logout():
    # TODO: wyczyść sesję (session.clear())
    session.clear()
    return redirect("/menu")


if __name__ == "__main__":
    app.run(debug=True)