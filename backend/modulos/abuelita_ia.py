
import re
import unicodedata

WHATSAPP = "7000-0000"
EMAIL = "pastelitosdelaabuela@gmail.com"


def _normalizar(texto):
    texto = unicodedata.normalize("NFD", (texto or "").lower())
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", texto).strip()


def _dinero(valor):
    return f"${float(valor):.2f}"


class AbuelitaIA:
    REGLAS = [
        (r"humano|persona|agente|asesor|hablar con alguien", "_humano"),
        (r"queja|reclamo|problema|\berror\b", "_queja"),
        (r"(costo|cuanto|cobran|cuesta|precio).*(envio|delivery|domicilio)"
         r"|(envio|delivery|domicilio).*(costo|cuanto|cobran|cuesta|precio)", "_costo_envio"),
        (r"modificar|cambiar (mi )?pedido|cancelar|cancelacion", "_modificar"),
        (r"minimo", "_minimo"),
        (r"historial|mis pedidos|pedidos anteriores", "_historial"),
        (r"tarda|demora|tiempo", "_tiempo"),
        (r"delivery|domicilio|envio|entrega|reparto", "_delivery"),
        (r"zona|cobertura|llegan|sector", "_zona"),
        (r"retiro|recoger|tienda|sucursal|\blocal\b", "_retiro"),
        (r"horario|\bhoras?\b|abren|cierran|atienden|domingo|sabado", "_horario"),
        (r"\bpuntos?\b|fidelidad|premio", "_puntos"),
        (r"\bpago|pagar|tarjeta|efectivo|transferencia", "_pagos"),
        (r"combo|promo|descuento|oferta", "_promos"),
        (r"recomiend|mas vendido|favorito|popular", "_recomendados"),
        (r"gluten|celiac|vegetarian|vegan|sin carne", "_dieta"),
        (r"evento|cumpleanos|fiesta|encargo", "_eventos"),
        (r"budin", "_budin"),
        (r"sabor|relleno|variedad", "_sabores"),
        (r"ingrediente|hechos?\b|preparan|\bmasa\b|de que estan", "_ingredientes"),
        (r"\bstock\b|hay hoy|queda|disponibilidad", "_stock"),
        (r"precio|cuanto|cuesta|\bvale\b|costo", "_precios"),
        (r"menu|producto|tienen|venden|catalogo|disponible", "_menu"),
        (r"pedido|pedir|comprar|compra|ordenar|carrito", "_pedido"),
        (r"contrasena|password|olvide", "_password"),
        (r"registr|crear cuenta|\bcuenta\b", "_registro"),
        (r"whatsapp|numero|telefono|contacto|correo|email", "_contacto"),
        (r"facebook|instagram|redes|tiktok", "_redes"),
        (r"gracias|grax|thanks", "_gracias"),
        (r"\b(hola|buenas|buenos|hey|saludos?)\b", "_saludo"),
    ]

    def responder(self, mensaje, productos=None):
        texto = _normalizar(mensaje)
        self._productos = productos or []
        if not texto:
            return "¡Hola, mi corazón! Escribe o selecciona una pregunta para poder ayudarte 👵🏼"
        for patron, metodo in self.REGLAS:
            if re.search(patron, texto):
                return getattr(self, metodo)()
        return self._no_entiendo()

    # 
    # Respuestas que dependen de la base de datos
    def _lista_productos(self):
        return "\n".join(
            f"• {p['nombre']} ({_dinero(p['precio'])})" for p in self._productos
        )

    def _menu(self):
        if not self._productos:
            return (f"Estamos actualizando nuestro menú 🧡 Escríbenos por WhatsApp al "
                    f"{WHATSAPP} para conocer lo disponible hoy.")
        return ("Nuestro menú incluye:\n" + self._lista_productos() +
                "\n\n¡Todo hecho con receta de la abuela! 🧡")

    def _precios(self):
        if not self._productos:
            return f"Escríbenos por WhatsApp al {WHATSAPP} y te pasamos la lista de precios 🥰"
        return ("Nuestros precios:\n" + self._lista_productos() +
                "\n\n¡Siempre con ingredientes frescos! 🥰")

    def _ingredientes(self):
        con_ing = [p for p in self._productos if (p.get("ingredientes") or "").strip()]
        if con_ing:
            lineas = "\n".join(f"• {p['nombre']}: {p['ingredientes'].strip()}" for p in con_ing)
            return "Esto es lo que lleva cada producto:\n" + lineas + "\n\n¡Sin conservantes! 🌾"
        return ("Nuestros pastelitos se preparan con masa artesanal y "
                "queso fresco de la casa. ¡Receta original de la abuela, "
                "sin conservantes! 🌾")

    def _stock(self):
        disponibles = [p for p in self._productos if (p.get("stock") or 0) > 0]
        if disponibles:
            lineas = "\n".join(f"• {p['nombre']}: {p['stock']} disponibles" for p in disponibles)
            return "Esto es lo que tenemos ahora mismo:\n" + lineas + "\n\n✅"
        return ("Para confirmar disponibilidad del día, "
                f"escríbenos por WhatsApp al {WHATSAPP} ✅")

    # Respuestas fijas
    
    def _sabores(self):
        return ("Sabores de pastelitos disponibles:\n"
                "• Queso 🧀\n• Pollo 🍗\n• Leche 🥛 (el clásico de la abuela)\n\n"
                "También tenemos calzone, pizza y budín casero.")

    def _budin(self):
        return ("Nuestro budín es casero, esponjoso y hecho con receta de la abuela. "
                "Pregúntanos por los sabores disponibles del día 🍞")

    def _pedido(self):
        return ("¡Hacer tu pedido es muy fácil!\n"
                "1️⃣ Regístrate o inicia sesión\n"
                "2️⃣ Elige tus productos del catálogo\n"
                "3️⃣ Agrégalos al carrito\n"
                "4️⃣ Confirma tu pedido y nosotros lo preparamos 🧡")

    def _promos(self):
        return ("🎁 Promociones especiales:\n"
                "• Docena de pastelitos con precio especial\n"
                "• Combos familiares (pizza + pastelitos)\n\n"
                f"Escríbenos por WhatsApp al {WHATSAPP} para ver las promos vigentes.")

    def _recomendados(self):
        return ("⭐ Lo más pedido:\n"
                "1. Pastelito de queso (el clásico)\n"
                "2. Pastelito de pollo\n"
                "3. Pizza artesanal\n\n"
                "¡No te vas a arrepentir! 😋")

    def _dieta(self):
        return ("Por ahora no tenemos línea sin gluten certificada, pero sí "
                "opciones vegetarianas (queso, pizza de vegetales). "
                f"Consúltanos por WhatsApp al {WHATSAPP} para detalles 🌱")

    def _pagos(self):
        return ("Formas de pago aceptadas:\n"
                "🏦 Transferencia bancaria\n"
                "💵 Contra entrega (efectivo)\n"
                "📱 Pago coordinado por WhatsApp")

    def _delivery(self):
        return ("🛵 Sí, hacemos entregas a domicilio.\n"
                "Zonas y costos se confirman por WhatsApp según tu ubicación.\n"
                "También puedes retirar en tienda sin costo.")

    def _zona(self):
        return ("📍 Cubrimos la zona central y alrededores. "
                "Escríbenos por WhatsApp con tu dirección para confirmar cobertura.")

    def _costo_envio(self):
        return ("El costo de envío depende de tu zona. "
                f"Escríbenos por WhatsApp al {WHATSAPP} y te lo confirmamos al instante 🛵")

    def _retiro(self):
        return ("🏪 Puedes retirar en tienda sin costo. "
                "Te avisamos por WhatsApp cuando tu pedido esté listo.")

    def _horario(self):
        return ("🕘 Nuestro horario:\n"
                "• Lunes a viernes: 9:00 AM – 8:00 PM\n"
                "• Sábados: 10:00 AM – 6:00 PM\n"
                "• Domingos: cerrado")

    def _tiempo(self):
        return ("⏱️ Tiempo aproximado:\n"
                "• Retiro en tienda: 15–20 min\n"
                "• Delivery: 30–45 min según zona")

    def _minimo(self):
        return "No tenemos pedido mínimo, ¡puedes ordenar desde 1 pastelito! 🥟"

    def _modificar(self):
        return ("Si tu pedido aún no está en preparación, sí podemos modificarlo o cancelarlo. "
                f"Escríbenos por WhatsApp al {WHATSAPP} lo antes posible 📱")

    def _registro(self):
        return ("Registrarte es gratis y rápido:\n"
                "1️⃣ Haz clic en 'iniciar sesión'\n"
                "2️⃣ Pestaña 'Registrarse'\n"
                "3️⃣ Llena tus datos y listo ✅")

    def _password(self):
        return ("Si olvidaste tu contraseña, escríbenos por WhatsApp "
                "y te ayudamos a recuperar tu cuenta 🔑")

    def _historial(self):
        return ("Puedes ver tu historial iniciando sesión y entrando a "
                "'Mis pedidos' en tu cuenta de cliente 📜")

    def _contacto(self):
        return f"📱 Contáctanos:\n• WhatsApp: {WHATSAPP}\n• Email: {EMAIL}"

    def _redes(self):
        return "Síguenos en Facebook e Instagram como 'Pastelitos de la Abuela' 🧡"

    def _humano(self):
        return (f"¡Claro! Escríbenos por WhatsApp al {WHATSAPP} "
                "y te atenderá una persona del equipo 👵🏼")

    def _queja(self):
        return ("Lamentamos el inconveniente 🙏. "
                f"Escríbenos por WhatsApp al {WHATSAPP} y lo resolvemos enseguida.")

    def _puntos(self):
        return ("Estamos preparando un programa de puntos 🎯. "
                "¡Muy pronto podrás acumular y canjear premios!")

    def _eventos(self):
        return ("¡Sí! Hacemos pedidos especiales para eventos y cumpleaños 🎉. "
                "Escríbenos con anticipación por WhatsApp para cotizar.")

    def _gracias(self):
        return "¡De nada, mi corazón! Que disfrutes tus pastelitos 🧡👵🏼"

    def _saludo(self):
        return ("¡Hola, mi corazón! 👵🏼 ¿En qué te puedo ayudar?\n"
                "Puedes preguntarme por el menú, precios, cómo comprar o ingredientes.")

    def _no_entiendo(self):
        return ("Mmm, no estoy segura de eso, pero puedo ayudarte con:\n"
                "• 📋 Menú y productos\n• 💲 Precios\n• 🛒 Cómo hacer tu pedido\n"
                "• 🌾 Ingredientes\n• 🛵 Delivery\n• 💳 Formas de pago\n\n"
                "Prueba con una de esas opciones 😊")


def guardar_historial(id_usuario, mensaje, respuesta):
    try:
        from modulos.conexion import Conexion
        instancia = Conexion()
        conn = instancia.conectar()
        if not conn:
            return
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO historial_chat (id_usuario, mensaje_usuario, respuesta_ia) "
            "VALUES (%s, %s, %s)",
            (id_usuario, mensaje, respuesta),
        )
        conn.commit()
        cursor.close()
        instancia.desconectar()
    except Exception as e:
        print(f"No se pudo guardar el historial del chat: {e}")