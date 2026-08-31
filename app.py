from flask import Flask, render_template, request, redirect, url_for, session, flash
from database import obtener_conexion
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)

# Clave para las sesiones
app.secret_key = "turissv_clave_secreta_2026"


# =====================================================
# PÁGINA PRINCIPAL
# =====================================================

@app.route("/")
def inicio():

    return render_template("index.html")


# =====================================================
# REGISTRO
# =====================================================

@app.route("/registro", methods=["GET", "POST"])
def registro():

    if request.method == "POST":

        nombre = request.form.get("nombre")
        correo = request.form.get("correo")
        telefono = request.form.get("telefono")
        password = request.form.get("password")
        confirmar = request.form.get("confirmar")


        # Comprobar que las contraseñas coincidan

        if password != confirmar:

            flash("Las contraseñas no coinciden.", "error")

            return redirect(url_for("registro"))


        conexion = None
        cursor = None

        try:

            conexion = obtener_conexion()

            cursor = conexion.cursor()


            # Comprobar si el correo ya existe

            cursor.execute(
                """
                SELECT id
                FROM usuarios
                WHERE correo = %s
                """,
                (correo,)
            )

            usuario_existente = cursor.fetchone()


            if usuario_existente:

                flash(
                    "El correo electrónico ya está registrado.",
                    "error"
                )

                return redirect(url_for("registro"))


            # Encriptar contraseña

            password_segura = generate_password_hash(password)


            # Insertar usuario

            cursor.execute(
                """
                INSERT INTO usuarios
                (
                    nombre_completo,
                    correo,
                    telefono,
                    password
                )
                VALUES (%s, %s, %s, %s)
                """,
                (
                    nombre,
                    correo,
                    telefono,
                    password_segura
                )
            )


            conexion.commit()


            flash(
                "¡Cuenta creada correctamente! Ahora inicia sesión.",
                "success"
            )

            return redirect(url_for("login"))


        except Exception as error:

            print("ERROR:", error)

            flash(
                "Ocurrió un error al crear la cuenta.",
                "error"
            )

            return redirect(url_for("registro"))


        finally:

            if cursor:
                cursor.close()

            if conexion:
                conexion.close()


    return render_template("registro.html")


# =====================================================
# INICIO DE SESIÓN
# =====================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        correo = request.form.get("correo")
        password = request.form.get("password")


        conexion = None
        cursor = None

        try:

            conexion = obtener_conexion()

            cursor = conexion.cursor(dictionary=True)


            cursor.execute(
                """
                SELECT *
                FROM usuarios
                WHERE correo = %s
                """,
                (correo,)
            )


            usuario = cursor.fetchone()


            # Comprobar usuario y contraseña

            if usuario and check_password_hash(
                usuario["password"],
                password
            ):

                # Guardar datos en sesión

                session["usuario_id"] = usuario["id"]

                session["nombre"] = usuario["nombre_completo"]

                session["correo"] = usuario["correo"]

                session["rol"] = usuario["rol"]


                # Ir al dashboard

                return redirect(
                    url_for("dashboard")
                )


            flash(
                "Correo o contraseña incorrectos.",
                "error"
            )

            return redirect(
                url_for("login")
            )


        except Exception as error:

            print("ERROR:", error)

            flash(
                "No se pudo conectar con la base de datos.",
                "error"
            )

            return redirect(
                url_for("login")
            )


        finally:

            if cursor:
                cursor.close()

            if conexion:
                conexion.close()


    return render_template("login.html")


# =====================================================
# DASHBOARD DEL USUARIO
# =====================================================

@app.route("/dashboard")
def dashboard():

    # Si no inició sesión
    if "usuario_id" not in session:

        return redirect(
            url_for("login")
        )


    return render_template(
        "dashboard.html",

        nombre=session["nombre"],

        correo=session["correo"]
    )


# =====================================================
# CERRAR SESIÓN
# =====================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("inicio")
    )


# =====================================================
# EJECUTAR APLICACIÓN
# =====================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )