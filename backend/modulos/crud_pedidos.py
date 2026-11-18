from datetime import timedelta
from decimal import Decimal
from modulos.conexion import Conexion

ENVIO = Decimal("1.00")          
ESTADO_RECIBIDO = 1
ESTADO_ENTREGADO = 4
ESTADO_CANCELADO = 5
DIAS = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]


def _cerrar(cursor, instancia):
    if cursor is not None:
        try:
            cursor.close()
        except Exception:
            pass
    instancia.desconectar()


def _formatear_fecha(fila):
    f = fila.get("fecha_pedido")
    if f is not None and hasattr(f, "strftime"):
        fila["fecha_pedido"] = f.strftime("%d/%m/%y %I:%M %p")
    return fila


class CRUDPedidos:
    def __init__(self):
        pass

    
    # Crear pedido (cliente)
  
    def crear_pedido(self, id_usuario, items, direccion, ciudad, referencia, metodo_pago):
        
        instancia = Conexion()
        conn = instancia.conectar()
        if not conn:
            return False, "Error de conexión a la base de datos."

        cursor = None
        try:
            cantidades = {}
            for it in items:
                pid = int(it.get("id_producto"))
                cant = int(it.get("cantidad"))
                if cant < 1 or cant > 99:
                    return False, "Cantidad no válida."
                cantidades[pid] = cantidades.get(pid, 0) + cant
            if not cantidades:
                return False, "Tu carrito está vacío."

            cursor = conn.cursor(dictionary=True)
            ids = sorted(cantidades)
            marcadores = ",".join(["%s"] * len(ids))
            cursor.execute(
                "SELECT id_producto, nombre, precio, stock FROM productos "
                f"WHERE estado = 1 AND id_producto IN ({marcadores}) "
                "ORDER BY id_producto FOR UPDATE",
                ids,
            )
            productos = {p["id_producto"]: p for p in cursor.fetchall()}

            subtotal = Decimal("0.00")
            lineas = []
            for pid in ids:
                p = productos.get(pid)
                if not p:
                    conn.rollback()
                    return False, "Uno de los productos ya no está disponible."
                cant = cantidades[pid]
                disponible = p["stock"] or 0
                if disponible < cant:
                    conn.rollback()
                    return False, f"Stock insuficiente de {p['nombre']} (quedan {disponible})."
                precio = Decimal(p["precio"])
                sub = precio * cant
                subtotal += sub
                lineas.append((pid, cant, precio, sub))

            total = subtotal + ENVIO

            cursor.execute(
                "INSERT INTO direcciones (id_usuario, direccion, ciudad, referencia) "
                "VALUES (%s, %s, %s, %s)",
                (id_usuario, direccion, ciudad, referencia or None),
            )
            id_direccion = cursor.lastrowid

            cursor.execute(
                "INSERT INTO pedidos (id_usuario, id_direccion, id_estado, subtotal, envio, total) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                (id_usuario, id_direccion, ESTADO_RECIBIDO, subtotal, ENVIO, total),
            )
            id_pedido = cursor.lastrowid

            for pid, cant, precio, sub in lineas:
                cursor.execute(
                    "INSERT INTO detalle_pedido (id_pedido, id_producto, cantidad, precio_unitario, subtotal) "
                    "VALUES (%s, %s, %s, %s, %s)",
                    (id_pedido, pid, cant, precio, sub),
                )
                cursor.execute(
                    "UPDATE productos SET stock = stock - %s WHERE id_producto = %s",
                    (cant, pid),
                )

            cursor.execute(
                "INSERT INTO pagos (id_pedido, metodo_pago, monto, estado_pago) "
                "VALUES (%s, %s, %s, 'Pendiente')",
                (id_pedido, metodo_pago, total),
            )

            conn.commit()
            return True, {
                "id_pedido": id_pedido,
                "subtotal": float(subtotal),
                "envio": float(ENVIO),
                "total": float(total),
            }
        except (TypeError, ValueError):
            conn.rollback()
            return False, "Datos del carrito no válidos."
        except Exception as e:
            conn.rollback()
            print(f"Error al crear pedido: {e}")
            return False, "No se pudo registrar el pedido. Inténtalo de nuevo."
        finally:
            _cerrar(cursor, instancia)

    
    # Consultas

    def obtener_pedidos_usuario(self, id_usuario):
        instancia = Conexion()
        conn = instancia.conectar()
        if not conn:
            return []
        cursor = None
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT p.id_pedido, p.fecha_pedido, p.total, p.id_estado,
                       e.nombre_estado AS estado,
                       (SELECT GROUP_CONCAT(CONCAT(d.cantidad, ' x ', pr.nombre) SEPARATOR ', ')
                          FROM detalle_pedido d
                          JOIN productos pr ON pr.id_producto = d.id_producto
                         WHERE d.id_pedido = p.id_pedido) AS productos
                FROM pedidos p
                JOIN estados_pedido e ON e.id_estado = p.id_estado
                WHERE p.id_usuario = %s
                ORDER BY p.fecha_pedido DESC, p.id_pedido DESC
                """,
                (id_usuario,),
            )
            return [_formatear_fecha(f) for f in cursor.fetchall()]
        except Exception as e:
            print(f"Error al obtener pedidos del usuario: {e}")
            return []
        finally:
            _cerrar(cursor, instancia)

    def obtener_todos_pedidos(self):
        instancia = Conexion()
        conn = instancia.conectar()
        if not conn:
            return []
        cursor = None
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT p.id_pedido, p.fecha_pedido, p.total, p.id_estado,
                       e.nombre_estado AS estado,
                       CONCAT(u.nombre, ' ', u.apellido) AS cliente,
                       (SELECT GROUP_CONCAT(CONCAT(d.cantidad, ' x ', pr.nombre) SEPARATOR ', ')
                          FROM detalle_pedido d
                          JOIN productos pr ON pr.id_producto = d.id_producto
                         WHERE d.id_pedido = p.id_pedido) AS productos
                FROM pedidos p
                JOIN estados_pedido e ON e.id_estado = p.id_estado
                JOIN usuarios u ON u.id_usuario = p.id_usuario
                ORDER BY p.fecha_pedido DESC, p.id_pedido DESC
                """
            )
            return [_formatear_fecha(f) for f in cursor.fetchall()]
        except Exception as e:
            print(f"Error al obtener pedidos: {e}")
            return []
        finally:
            _cerrar(cursor, instancia)

    def obtener_estados(self):
        instancia = Conexion()
        conn = instancia.conectar()
        if not conn:
            return []
        cursor = None
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id_estado, nombre_estado FROM estados_pedido ORDER BY id_estado")
            return cursor.fetchall()
        except Exception as e:
            print(f"Error al obtener estados: {e}")
            return []
        finally:
            _cerrar(cursor, instancia)

    
    # Cambiar estado (admin)
    
    def cambiar_estado(self, id_pedido, id_estado):
        instancia = Conexion()
        conn = instancia.conectar()
        if not conn:
            return False, "Error de conexión."
        cursor = None
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT id_estado FROM pedidos WHERE id_pedido = %s FOR UPDATE", (id_pedido,)
            )
            pedido = cursor.fetchone()
            if not pedido:
                conn.rollback()
                return False, "Pedido no encontrado."
            if pedido["id_estado"] == ESTADO_CANCELADO:
                conn.rollback()
                return False, "Un pedido cancelado ya no se puede modificar."

            cursor.execute("SELECT id_estado FROM estados_pedido WHERE id_estado = %s", (id_estado,))
            if not cursor.fetchone():
                conn.rollback()
                return False, "Estado no válido."

            if id_estado == ESTADO_CANCELADO:
                # Devolver el stock de lo que se había descontado
                cursor.execute(
                    "SELECT id_producto, cantidad FROM detalle_pedido WHERE id_pedido = %s",
                    (id_pedido,),
                )
                for d in cursor.fetchall():
                    cursor.execute(
                        "UPDATE productos SET stock = stock + %s WHERE id_producto = %s",
                        (d["cantidad"], d["id_producto"]),
                    )
                cursor.execute(
                    "UPDATE pagos SET estado_pago = 'Cancelado' WHERE id_pedido = %s", (id_pedido,)
                )
            elif id_estado == ESTADO_ENTREGADO:
                cursor.execute(
                    "UPDATE pagos SET estado_pago = 'Pagado' WHERE id_pedido = %s", (id_pedido,)
                )

            cursor.execute(
                "UPDATE pedidos SET id_estado = %s WHERE id_pedido = %s", (id_estado, id_pedido)
            )
            conn.commit()
            return True, "Estado del pedido actualizado."
        except Exception as e:
            conn.rollback()
            print(f"Error al cambiar estado del pedido: {e}")
            return False, "No se pudo actualizar el pedido."
        finally:
            _cerrar(cursor, instancia)

   
    # Estadísticas del panel de inicio (admin)
   
    def estadisticas(self):
        vacio = {"pedidos_hoy": 0, "clientes": 0, "ventas_total": 0.0,
                 "semana": {"labels": [], "valores": []}}
        instancia = Conexion()
        conn = instancia.conectar()
        if not conn:
            return vacio
        cursor = None
        try:
            cursor = conn.cursor(dictionary=True)

            cursor.execute("SELECT CURDATE() AS hoy")
            hoy = cursor.fetchone()["hoy"]

            cursor.execute(
                "SELECT COUNT(*) AS n FROM pedidos WHERE DATE(fecha_pedido) = CURDATE() AND id_estado <> %s",
                (ESTADO_CANCELADO,),
            )
            pedidos_hoy = cursor.fetchone()["n"]

            cursor.execute("SELECT COUNT(*) AS n FROM usuarios WHERE id_rol = 2")
            clientes = cursor.fetchone()["n"]

            cursor.execute(
                "SELECT COALESCE(SUM(total), 0) AS t FROM pedidos WHERE id_estado <> %s",
                (ESTADO_CANCELADO,),
            )
            ventas_total = float(cursor.fetchone()["t"])

            cursor.execute(
                "SELECT DATE(fecha_pedido) AS d, SUM(total) AS t FROM pedidos "
                "WHERE fecha_pedido >= CURDATE() - INTERVAL 6 DAY AND id_estado <> %s "
                "GROUP BY DATE(fecha_pedido)",
                (ESTADO_CANCELADO,),
            )
            por_dia = {fila["d"]: float(fila["t"]) for fila in cursor.fetchall()}

            labels, valores = [], []
            for i in range(6, -1, -1):
                dia = hoy - timedelta(days=i)
                labels.append(f"{DIAS[dia.weekday()]} {dia.day}")
                valores.append(round(por_dia.get(dia, 0.0), 2))

            return {
                "pedidos_hoy": pedidos_hoy,
                "clientes": clientes,
                "ventas_total": ventas_total,
                "semana": {"labels": labels, "valores": valores},
            }
        except Exception as e:
            print(f"Error al calcular estadísticas: {e}")
            return vacio
        finally:
            _cerrar(cursor, instancia)