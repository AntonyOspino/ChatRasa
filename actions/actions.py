from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
import psycopg2
from dotenv import load_dotenv
import os

# cargar variables de entorno .env
load_dotenv()
# otener la cadena de conexion
connection_string = os.getenv("NEON_CONNECTION_STRING")

def get_connection():
    return psycopg2.connect(connection_string)


# Citas
class ActionConsultarCita(Action):
    def name(self):
        return "action_consultar_cita"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict):
        conn = None
        cursor = None
        try:
            identificacion = tracker.get_slot("identificacion")
            print(f" DEBUG - Identificacion en slot: {identificacion}")

            # Si no hay identificación, intentar obtenerlo del último mensaje
            if not identificacion:
                texto = tracker.latest_message.get("text")
                if texto.isdigit() and len(texto) >= 6:
                    identificacion = texto

            if not identificacion or not identificacion.isdigit():
                dispatcher.utter_message(text="⚠️ Por favor, ingresa un número de identificación válido (solo dígitos).")
                return []

            conn = get_connection()
            cursor = conn.cursor()

            # Buscar el usuario con esa identificación
            cursor.execute("""
                SELECT id FROM usuario WHERE identificacion = %s;
            """, (identificacion,))
            usuario = cursor.fetchone()

            if not usuario:
                dispatcher.utter_message(text="❌ No encontré ningún usuario con esa identificación.")
                return []

            usuario_id = usuario[0]

            # Buscar citas activas de ese usuario
            cursor.execute("""
                SELECT fecha_cita, hora_cita 
                FROM cita 
                WHERE usuario_paciente_id = %s 
                AND estado = 'Aprobada'
                ORDER BY fecha_cita ASC;
            """, (usuario_id,))

            citas = cursor.fetchall()

            if citas:
                mensajes = []
                for cita in citas:
                    fecha, hora = cita
                    mensajes.append(f"{fecha} a las {hora}")
                if len(citas) == 1:
                    mensaje_final = f"Tienes una cita activa el {citas[0][0]} a las {citas[0][1]}"
                else:
                    mensaje_final = "Estas son tus citas activas:\n" + "\n".join(mensajes)
                dispatcher.utter_message(text=mensaje_final)
            else:
                dispatcher.utter_message(text="No tienes citas activas registradas 🗓️")
                
        except Exception as e:
            dispatcher.utter_message(text=f"⚠️ Error al consultar la base de datos: {e}")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

        return []
class ActionConsultarCitasAnteriores(Action):
    def name(self):
        return "action_consultar_citas_anteriores"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict):
        conn = None
        cursor = None
        try:
            identificacion = tracker.get_slot("identificacion")
            
            if not identificacion:
                texto = tracker.latest_message.get("text")
                if texto and texto.isdigit() and len(texto) >= 6:
                    identificacion = texto

            if not identificacion or not identificacion.isdigit():
                dispatcher.utter_message(text="⚠️ Por favor, ingresa un número de identificación válido.")
                return []

            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT id FROM usuario WHERE identificacion = %s;", (identificacion,))
            usuario = cursor.fetchone()

            if not usuario:
                dispatcher.utter_message(text="❌ No encontré ningún usuario con esa identificación.")
                return []

            usuario_id = usuario[0]

            # Obtener citas atendidas
            cursor.execute("""
                SELECT c.fecha_cita, c.hora_cita, e.nombre as especialidad,
                       u.nombre, u.apellido
                FROM cita c
                JOIN especialidad e ON c.especialidad_id = e.id
                LEFT JOIN usuario u ON c.usuario_medico_id = u.id
                WHERE c.usuario_paciente_id = %s 
                  AND c.estado = 'Atendida'
                ORDER BY c.fecha_cita DESC
                LIMIT 5;
            """, (usuario_id,))

            citas = cursor.fetchall()

            if citas:
                mensaje = "📅 **Tus últimas citas atendidas:**\n\n"
                for cita in citas:
                    fecha, hora, especialidad, nombre_med, apellido_med = cita
                    medico = f"Dr./Dra. {nombre_med} {apellido_med}" if nombre_med else "No especificado"
                    mensaje += f"📆 {fecha} a las {hora}\n"
                    mensaje += f"🏥 Especialidad: {especialidad}\n"
                    mensaje += f"👨‍⚕️ Médico: {medico}\n"
                    mensaje += "─" * 40 + "\n\n"
                dispatcher.utter_message(text=mensaje)
            else:
                dispatcher.utter_message(text="No tienes citas atendidas registradas 📋")
                
        except Exception as e:
            dispatcher.utter_message(text=f"⚠️ Error al consultar citas anteriores: {e}")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

        return []
class ActionConsultarProximaCita(Action):
    def name(self):
        return "action_consultar_proxima_cita"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict):
        conn = None
        cursor = None
        try:
            identificacion = tracker.get_slot("identificacion")
            
            if not identificacion:
                texto = tracker.latest_message.get("text")
                if texto and texto.isdigit() and len(texto) >= 6:
                    identificacion = texto

            if not identificacion or not identificacion.isdigit():
                dispatcher.utter_message(text="⚠️ Por favor, ingresa un número de identificación válido.")
                return []

            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT id FROM usuario WHERE identificacion = %s;", (identificacion,))
            usuario = cursor.fetchone()

            if not usuario:
                dispatcher.utter_message(text="❌ No encontré ningún usuario con esa identificación.")
                return []

            usuario_id = usuario[0]

            # Obtener la próxima cita más cercana
            cursor.execute("""
                SELECT c.fecha_cita, c.hora_cita, e.nombre as especialidad,
                       u.nombre, u.apellido
                FROM cita c
                JOIN especialidad e ON c.especialidad_id = e.id
                LEFT JOIN usuario u ON c.usuario_medico_id = u.id
                WHERE c.usuario_paciente_id = %s 
                  AND c.estado = 'Aprobada'
                  AND c.fecha_cita >= CURRENT_DATE
                ORDER BY c.fecha_cita ASC, c.hora_cita ASC
                LIMIT 1;
            """, (usuario_id,))

            cita = cursor.fetchone()

            if cita:
                fecha, hora, especialidad, nombre_med, apellido_med = cita
                medico = f"Dr./Dra. {nombre_med} {apellido_med}" if nombre_med else "No especificado"
                mensaje = f"📅 **Tu próxima cita:**\n\n"
                mensaje += f"📆 Fecha: {fecha}\n"
                mensaje += f"⏰ Hora: {hora}\n"
                mensaje += f"🏥 Especialidad: {especialidad}\n"
                mensaje += f"👨‍⚕️ Médico: {medico}"
                dispatcher.utter_message(text=mensaje)
            else:
                dispatcher.utter_message(text="No tienes citas próximas programadas 📅")
                
        except Exception as e:
            dispatcher.utter_message(text=f"⚠️ Error al consultar próxima cita: {e}")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

        return []

# Historial
class ActionConsultarHistorial(Action):
    def name(self):
        return "action_consultar_historial"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict):
        conn = None
        cursor = None
        try:
            identificacion = tracker.get_slot("identificacion")
            
            if not identificacion:
                texto = tracker.latest_message.get("text")
                if texto and texto.isdigit() and len(texto) >= 6:
                    identificacion = texto

            if not identificacion or not identificacion.isdigit():
                dispatcher.utter_message(text="⚠️ Por favor, ingresa un número de identificación válido.")
                return []

            conn = get_connection()
            cursor = conn.cursor()

            # Buscar el usuario
            cursor.execute("SELECT id FROM usuario WHERE identificacion = %s;", (identificacion,))
            usuario = cursor.fetchone()

            if not usuario:
                dispatcher.utter_message(text="❌ No encontré ningún usuario con esa identificación.")
                return []

            usuario_id = usuario[0]

            # Obtener historial médico
            cursor.execute("""
                SELECT hm.diagnostico, hm.recomendaciones, hm.sistema, 
                       c.fecha_cita, hm.fecha_creacion
                FROM historial_medico hm
                JOIN cita c ON hm.cita_id = c.id
                WHERE c.usuario_paciente_id = %s
                ORDER BY hm.fecha_creacion DESC
                LIMIT 5;
            """, (usuario_id,))

            historiales = cursor.fetchall()

            if historiales:
                mensaje = "📋 **Tu historial médico reciente:**\n\n"
                for hist in historiales:
                    diagnostico, recomendaciones, sistema, fecha_cita, fecha_creacion = hist
                    mensaje += f"📅 Fecha: {fecha_cita}\n"
                    mensaje += f"🔍 Sistema: {sistema}\n"
                    mensaje += f"💊 Diagnóstico: {diagnostico}\n"
                    mensaje += f"📝 Recomendaciones: {recomendaciones}\n"
                    mensaje += "─" * 40 + "\n\n"
                dispatcher.utter_message(text=mensaje)
            else:
                dispatcher.utter_message(text="No tienes historial médico registrado aún 📋")
                
        except Exception as e:
            dispatcher.utter_message(text=f"⚠️ Error al consultar historial: {e}")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

        return []

# Diagnostico
class ActionConsultarUltimoDiagnostico(Action):
    def name(self):
        return "action_consultar_ultimo_diagnostico"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict):
        conn = None
        cursor = None
        try:
            identificacion = tracker.get_slot("identificacion")
            
            if not identificacion:
                texto = tracker.latest_message.get("text")
                if texto and texto.isdigit() and len(texto) >= 6:
                    identificacion = texto

            if not identificacion or not identificacion.isdigit():
                dispatcher.utter_message(text="⚠️ Por favor, ingresa un número de identificación válido.")
                return []

            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT id FROM usuario WHERE identificacion = %s;", (identificacion,))
            usuario = cursor.fetchone()

            if not usuario:
                dispatcher.utter_message(text="❌ No encontré ningún usuario con esa identificación.")
                return []

            usuario_id = usuario[0]

            # Obtener último diagnóstico
            cursor.execute("""
                SELECT hm.diagnostico, hm.sistema, c.fecha_cita, 
                       u.nombre, u.apellido
                FROM historial_medico hm
                JOIN cita c ON hm.cita_id = c.id
                LEFT JOIN usuario u ON c.usuario_medico_id = u.id
                WHERE c.usuario_paciente_id = %s
                ORDER BY hm.fecha_creacion DESC
                LIMIT 1;
            """, (usuario_id,))

            diagnostico = cursor.fetchone()

            if diagnostico:
                diag, sistema, fecha, nombre_med, apellido_med = diagnostico
                medico = f"Dr./Dra. {nombre_med} {apellido_med}" if nombre_med else "No especificado"
                mensaje = f"🩺 **Último diagnóstico:**\n\n"
                mensaje += f"📅 Fecha: {fecha}\n"
                mensaje += f"👨‍⚕️ Médico: {medico}\n"
                mensaje += f"🔍 Sistema evaluado: {sistema}\n"
                mensaje += f"💊 Diagnóstico: {diag}"
                dispatcher.utter_message(text=mensaje)
            else:
                dispatcher.utter_message(text="No tienes diagnósticos registrados todavía 🩺")
                
        except Exception as e:
            dispatcher.utter_message(text=f"⚠️ Error al consultar diagnóstico: {e}")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

        return []

# Medicos
class ActionConsultarDoctor(Action):
    def name(self):
        return "action_consultar_doctor"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: dict):

        identificacion = tracker.get_slot("identificacion")

        # Si no hay identificación, intentar obtenerlo del último mensaje
        if not identificacion or not identificacion.isdigit() or len(identificacion) < 6:
            texto = tracker.latest_message.get("text")
            if texto and texto.isdigit() and len(texto) >= 6:
                identificacion = texto

        if not identificacion or not identificacion.isdigit():
                dispatcher.utter_message(text="⚠️ Por favor, ingresa un número de identificación válido (solo dígitos).")
                return []

        try:
            # Conexión a PostgreSQL (ajusta tus credenciales si es necesario)
            conn = get_connection()
            cursor = conn.cursor()

            # 1️⃣ Buscar el ID del usuario (paciente)
            cursor.execute("""
                SELECT id FROM usuario WHERE identificacion = %s;
            """, (identificacion,))
            usuario = cursor.fetchone()

            if not usuario:
                dispatcher.utter_message(text="No encontré ningún paciente con esa identificación.")
                return []

            usuario_id = usuario[0]

            # 2️⃣ Buscar la cita más reciente aprobada del paciente
            cursor.execute("""
                SELECT usuario_medico_id 
                FROM cita 
                WHERE usuario_paciente_id = %s AND estado = 'Aprobada'
                ORDER BY fecha_cita DESC, hora_cita DESC
                LIMIT 1;
            """, (usuario_id,))
            cita = cursor.fetchone()

            if not cita:
                dispatcher.utter_message(text="No tienes ninguna cita aprobada actualmente.")
                return []

            usuario_medico_id = cita[0]

            # 3️⃣ Obtener los datos del médico
            cursor.execute("""
                SELECT nombre, apellido 
                FROM usuario 
                WHERE id = %s;
            """, (usuario_medico_id,))
            doctor = cursor.fetchone()

            if doctor:
                nombre_doctor = f"{doctor[0]} {doctor[1]}"
                dispatcher.utter_message(text=f"Tu médico asignado es el Dr./Dra. {nombre_doctor}")
            else:
                dispatcher.utter_message(text="No encontré los datos del médico asignado a tu cita.")

        except Exception as e:
            print("Error al consultar el doctor:", e)
            dispatcher.utter_message(text="Hubo un problema al consultar la información del médico.")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

        return []

# Especialidades
class ActionConsultarEspecialidades(Action):
    def name(self):
        return "action_consultar_especialidades"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict):
        conn = None
        cursor = None
        try:
            conn = get_connection()
            cursor = conn.cursor()

            # Obtener todas las especialidades
            cursor.execute("""
                SELECT nombre, descripcion 
                FROM especialidad 
                ORDER BY nombre;
            """)

            especialidades = cursor.fetchall()

            if especialidades:
                mensaje = "🏥 **Especialidades disponibles:**\n\n"
                for esp in especialidades:
                    nombre, descripcion = esp
                    mensaje += f"• **{nombre}**"
                    if descripcion:
                        mensaje += f": {descripcion}"
                    mensaje += "\n"
                dispatcher.utter_message(text=mensaje)
            else:
                dispatcher.utter_message(text="No hay especialidades registradas en el sistema 🏥")
                
        except Exception as e:
            dispatcher.utter_message(text=f"⚠️ Error al consultar especialidades: {e}")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

        return []

# Medicos Y Especialidades
class ActionConsultarMedicosEspecialidad(Action):
    def name(self):
        return "action_consultar_medicos_especialidad"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict):
        conn = None
        cursor = None
        try:
            # Intentar obtener la especialidad del mensaje
            texto = tracker.latest_message.get("text", "").lower()
            
            conn = get_connection()
            cursor = conn.cursor()

            # Buscar especialidad mencionada
            cursor.execute("SELECT id, nombre FROM especialidad;")
            especialidades = cursor.fetchall()
            
            especialidad_id = None
            especialidad_nombre = None
            
            for esp_id, esp_nombre in especialidades:
                if esp_nombre.lower() in texto:
                    especialidad_id = esp_id
                    especialidad_nombre = esp_nombre
                    break
            
            # Si no se encuentra especialidad en el texto, mostrar todas
            if not especialidad_id:
                cursor.execute("""
                    SELECT e.nombre, COUNT(m.medico_id) as cantidad
                    FROM especialidad e
                    LEFT JOIN medico m ON e.id = m.especialidad_id
                    GROUP BY e.nombre
                    ORDER BY e.nombre;
                """)
                
                datos = cursor.fetchall()
                
                if datos:
                    mensaje = "👨‍⚕️ **Médicos disponibles por especialidad:**\n\n"
                    for esp, cant in datos:
                        mensaje += f"🏥 {esp}: {cant} médico(s)\n"
                    mensaje += "\n💡 Tip: Menciona una especialidad específica para ver los médicos disponibles."
                    dispatcher.utter_message(text=mensaje)
                else:
                    dispatcher.utter_message(text="No hay información de médicos disponible 👨‍⚕️")
                return []
            
            # Si se encontró especialidad, mostrar médicos de esa especialidad
            cursor.execute("""
                SELECT u.nombre, u.apellido, u.correo
                FROM medico m
                JOIN usuario u ON m.medico_id = u.id
                WHERE m.especialidad_id = %s
                ORDER BY u.nombre;
            """, (especialidad_id,))
            
            medicos = cursor.fetchall()
            
            if medicos:
                mensaje = f"👨‍⚕️ **Médicos de {especialidad_nombre}:**\n\n"
                for nombre, apellido, correo in medicos:
                    mensaje += f"• Dr./Dra. {nombre} {apellido}\n"
                    mensaje += f"  📧 {correo}\n\n"
                dispatcher.utter_message(text=mensaje)
            else:
                dispatcher.utter_message(text=f"No hay médicos registrados en {especialidad_nombre} 👨‍⚕️")
                
        except Exception as e:
            dispatcher.utter_message(text=f"⚠️ Error al consultar médicos: {e}")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

        return []

# Datos del paciente
class ActionConsultarDatosPaciente(Action):
    def name(self):
        return "action_consultar_datos_paciente"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict):
        conn = None
        cursor = None
        try:
            identificacion = tracker.get_slot("identificacion")
            
            if not identificacion:
                texto = tracker.latest_message.get("text")
                if texto and texto.isdigit() and len(texto) >= 6:
                    identificacion = texto

            if not identificacion or not identificacion.isdigit():
                dispatcher.utter_message(text="⚠️ Por favor, ingresa un número de identificación válido.")
                return []

            conn = get_connection()
            cursor = conn.cursor()

            # Buscar usuario y datos de paciente
            cursor.execute("""
                SELECT u.nombre, u.apellido, u.edad, u.ciudad, u.pais,
                       p.tipo_paciente, p.enfermedades, p.peso, p.talla
                FROM usuario u
                LEFT JOIN paciente p ON u.id = p.usuario_id
                WHERE u.identificacion = %s;
            """, (identificacion,))

            datos = cursor.fetchone()

            if not datos:
                dispatcher.utter_message(text="❌ No encontré ningún usuario con esa identificación.")
                return []

            nombre, apellido, edad, ciudad, pais, tipo, enfermedades, peso, talla = datos

            mensaje = f"👤 **Datos del paciente:**\n\n"
            mensaje += f"📝 Nombre: {nombre} {apellido}\n"
            mensaje += f"🎂 Edad: {edad} años\n"
            mensaje += f"📍 Ubicación: {ciudad}, {pais}\n"
            
            if tipo:
                mensaje += f"🏷️ Tipo de paciente: {tipo}\n"
            if peso:
                mensaje += f"⚖️ Peso: {peso} kg\n"
            if talla:
                mensaje += f"📏 Talla: {talla} m\n"
            if enfermedades:
                mensaje += f"Enfermedades registradas: {enfermedades}\n"
            
            dispatcher.utter_message(text=mensaje)
                
        except Exception as e:
            dispatcher.utter_message(text=f"⚠️ Error al consultar datos del paciente: {e}")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

        return []

# Consulta recomendaciones
class ActionConsultarRecomendaciones(Action):
    def name(self):
        return "action_consultar_recomendaciones"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict):
        conn = None
        cursor = None
        try:
            identificacion = tracker.get_slot("identificacion")
            
            if not identificacion:
                texto = tracker.latest_message.get("text")
                if texto and texto.isdigit() and len(texto) >= 6:
                    identificacion = texto

            if not identificacion or not identificacion.isdigit():
                dispatcher.utter_message(text="⚠️ Por favor, ingresa un número de identificación válido.")
                return []

            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT id FROM usuario WHERE identificacion = %s;", (identificacion,))
            usuario = cursor.fetchone()

            if not usuario:
                dispatcher.utter_message(text="❌ No encontré ningún usuario con esa identificación.")
                return []

            usuario_id = usuario[0]

            # Obtener últimas recomendaciones
            cursor.execute("""
                SELECT hm.recomendaciones, hm.sistema, c.fecha_cita,
                       u.nombre, u.apellido
                FROM historial_medico hm
                JOIN cita c ON hm.cita_id = c.id
                LEFT JOIN usuario u ON c.usuario_medico_id = u.id
                WHERE c.usuario_paciente_id = %s
                ORDER BY hm.fecha_creacion DESC
                LIMIT 3;
            """, (usuario_id,))

            recomendaciones = cursor.fetchall()

            if recomendaciones:
                mensaje = "📝 **Tus últimas recomendaciones médicas:**\n\n"
                for rec in recomendaciones:
                    recom, sistema, fecha, nombre_med, apellido_med = rec
                    medico = f"Dr./Dra. {nombre_med} {apellido_med}" if nombre_med else "No especificado"
                    mensaje += f"📅 Fecha: {fecha}\n"
                    mensaje += f"👨‍⚕️ Médico: {medico}\n"
                    mensaje += f"🔍 Sistema: {sistema}\n"
                    mensaje += f"💡 Recomendación: {recom}\n"
                    mensaje += "─" * 40 + "\n\n"
                dispatcher.utter_message(text=mensaje)
            else:
                dispatcher.utter_message(text="No tienes recomendaciones médicas registradas 📝")
                
        except Exception as e:
            dispatcher.utter_message(text=f"⚠️ Error al consultar recomendaciones: {e}")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

        return []


