import json
import os
import random
from datetime import datetime
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

REVIEWS_FILE = "qa_reviews.json"
QUESTIONS_PER_GAME = 8

# Banco ampliado de 18 incidencias técnicas
QUESTIONS = [
    {
        "id": 1,
        "module": "NET_GATEWAY",
        "question": "Un cliente reporta que la API devuelve HTTP 502 Bad Gateway. ¿Cuál es la causa más probable?",
        "options": [
            "El cliente envió un JSON mal formado.",
            "El servidor proxy recibió una respuesta inválida del servidor upstream.",
            "El recurso solicitado fue movido permanentemente.",
            "El usuario no tiene permisos de administrador."
        ],
        "correct": 1,
        "hint": "Los errores 5xx son del lado del servidor; el 502 ocurre entre un proxy/balanceador y el backend."
    },
    {
        "id": 2,
        "module": "DB_CLUSTER",
        "question": "Una consulta SQL tarda 18 segundos en una tabla de 5 millones de filas al filtrar por 'email'. ¿Qué solución inmediata optimiza la lectura?",
        "options": [
            "Cambiar el tipo de dato de VARCHAR a TEXT.",
            "Agregar un índice (INDEX) en la columna 'email'.",
            "Ejecutar SELECT * sin cláusula WHERE.",
            "Duplicar la tabla en otra base de datos."
        ],
        "correct": 1,
        "hint": "Evita el 'Full Table Scan' creando una estructura de búsqueda rápida (árbol B) sobre esa columna."
    },
    {
        "id": 3,
        "module": "SEC_AUTH",
        "question": "¿Cuál es la práctica correcta para almacenar contraseñas de usuarios en producción?",
        "options": [
            "Texto plano con permisos de solo lectura.",
            "Cifrado Base64 reversible.",
            "Hash seguro con algoritmo lento (bcrypt o Argon2) y salt único.",
            "Hash MD5 sin salt para ahorrar CPU."
        ],
        "correct": 2,
        "hint": "MD5 es vulnerable a colisiones y Base64 es solo codificación. Busca hashing con 'salt'."
    },
    {
        "id": 4,
        "module": "OS_KERNEL",
        "question": "Dos procesos en el servidor se bloquean mutuamente esperando un recurso que el otro retiene. ¿Cómo se llama este fenómeno?",
        "options": [
            "Memory Leak",
            "Deadlock (Interbloqueo)",
            "Buffer Overflow",
            "Race Condition"
        ],
        "correct": 1,
        "hint": "Es un abrazo mortal donde ninguno puede avanzar porque espera que el otro libere su candado."
    },
    {
        "id": 5,
        "module": "ALGO_CORE",
        "question": "¿Qué complejidad temporal tiene la búsqueda binaria (Binary Search) sobre un arreglo ordenado?",
        "options": ["O(n)", "O(n²)", "O(log n)", "O(1)"],
        "correct": 2,
        "hint": "En cada paso divides el espacio de búsqueda exactamente a la mitad."
    },
    {
        "id": 6,
        "module": "NET_PROTO",
        "question": "¿Qué protocolo de capa de transporte garantiza entrega ordenada y retransmisión de paquetes perdidos?",
        "options": ["UDP", "ICMP", "TCP", "ARP"],
        "correct": 2,
        "hint": "Utiliza el famoso 'Three-Way Handshake' (SYN, SYN-ACK, ACK)."
    },
    {
        "id": 7,
        "module": "GIT_DEPLOY",
        "question": "Hiciste un commit con credenciales en una rama compartida. ¿Qué comando revierte los cambios sin reescribir el historial público?",
        "options": [
            "git revert",
            "git reset --hard",
            "git push --force",
            "git clean -fd"
        ],
        "correct": 0,
        "hint": "Crea un nuevo commit que deshace exactamente los cambios anteriores de forma segura."
    },
    {
        "id": 8,
        "module": "DOCKER_NODE",
        "question": "Un contenedor cae por 'OOMKilled' (Exit Code 137). ¿Qué recurso se agotó?",
        "options": [
            "Espacio en disco SSD.",
            "Memoria RAM asignada al contenedor.",
            "Ancho de banda de red.",
            "Puertos TCP disponibles."
        ],
        "correct": 1,
        "hint": "OOM significa literalmente 'Out Of Memory'."
    },
    {
        "id": 9,
        "module": "SEC_WEB",
        "question": "Un atacante inserta `' OR '1'='1` en el campo de login y logra entrar sin contraseña. ¿Qué vulnerabilidad explotó?",
        "options": [
            "Cross-Site Scripting (XSS)",
            "SQL Injection (SQLi)",
            "Denial of Service (DoS)",
            "Man-in-the-Middle (MitM)"
        ],
        "correct": 1,
        "hint": "Ocurre cuando se concatenan entradas del usuario directamente en consultas a la base de datos."
    },
    {
        "id": 10,
        "module": "LINUX_OPS",
        "question": "¿Qué comando de Linux te permite ver en tiempo real qué procesos consumen más CPU y memoria?",
        "options": ["chmod", "top / htop", "mkdir", "grep"],
        "correct": 1,
        "hint": "Es el equivalente en terminal al Administrador de Tareas."
    },
    {
        "id": 11,
        "module": "API_REST",
        "question": "¿Qué código de estado HTTP indica que el cliente superó el límite de peticiones permitidas (Rate Limiting)?",
        "options": [
            "401 Unauthorized",
            "404 Not Found",
            "429 Too Many Requests",
            "204 No Content"
        ],
        "correct": 2,
        "hint": "Es un error 4xx específicamente diseñado para frenar abuso de tráfico."
    },
    {
        "id": 12,
        "module": "DB_ACID",
        "question": "En transacciones de bases de datos (ACID), ¿qué garantiza la propiedad de Atomicidad?",
        "options": [
            "Que los datos se comprimen automáticamente.",
            "Que la transacción se ejecuta completa o no se aplica nada (todo o nada).",
            "Que cualquier usuario puede leer tablas sin permiso.",
            "Que la base de datos nunca necesita respaldos."
        ],
        "correct": 1,
        "hint": "Si falla el paso 3 de una transferencia bancaria, se revierten los pasos 1 y 2."
    },
    {
        "id": 13,
        "module": "NET_DNS",
        "question": "El servidor responde por su dirección IP, pero falla al acceder por su nombre de dominio. ¿Qué servicio está fallando?",
        "options": ["DHCP", "DNS", "SMTP", "FTP"],
        "correct": 1,
        "hint": "Es la 'agenda telefónica' de internet que traduce dominios a direcciones IP."
    },
    {
        "id": 14,
        "module": "CACHE_REDIS",
        "question": "La base de datos está saturada recibiendo miles de lecturas idénticas por segundo. ¿Qué componente alivia esa carga de inmediato?",
        "options": [
            "Una capa de caché en memoria (ej. Redis o Memcached).",
            "Aumentar el tamaño de los archivos de log.",
            "Desactivar HTTPS en el servidor.",
            "Convertir las tablas a formato CSV."
        ],
        "correct": 0,
        "hint": "Guardar resultados frecuentes en RAM evita consultar el disco una y otra vez."
    },
    {
        "id": 15,
        "module": "DATA_STRUCT",
        "question": "¿Qué estructura de datos sigue estrictamente el principio LIFO (Last In, First Out)?",
        "options": [
            "Cola (Queue)",
            "Pila (Stack)",
            "Grafo dirigido",
            "Tabla Hash"
        ],
        "correct": 1,
        "hint": "Piensa en una torre de platos: el último que pones arriba es el primero que sacas."
    },
    {
        "id": 16,
        "module": "WEB_CORS",
        "question": "El navegador bloquea una petición fetch de tu frontend hacia tu API en otro dominio. ¿Qué mecanismo de seguridad del navegador intervino?",
        "options": ["CORS", "SSH", "NAT", "RAID"],
        "correct": 0,
        "hint": "Significa Cross-Origin Resource Sharing y se controla con cabeceras HTTP como Access-Control-Allow-Origin."
    },
    {
        "id": 17,
        "module": "CLOUD_ARCH",
        "question": "¿Cuál es la función principal de un Load Balancer (Balanceador de Carga) en producción?",
        "options": [
            "Compilar el código fuente en cada petición.",
            "Distribuir el tráfico entrante entre múltiples servidores backend.",
            "Borrar automáticamente usuarios inactivos.",
            "Reemplazar el sistema operativo del servidor."
        ],
        "correct": 1,
        "hint": "Evita que un solo servidor se sature repartiendo las peticiones entre varios nodos."
    },
    {
        "id": 18,
        "module": "LINUX_PERM",
        "question": "Un script `.sh` no se ejecuta en Linux y arroja 'Permission denied'. ¿Qué comando le otorga permiso de ejecución?",
        "options": [
            "chmod +x script.sh",
            "rm -rf script.sh",
            "ping script.sh",
            "cat script.sh"
        ],
        "correct": 0,
        "hint": "Modifica los bits de permisos agregando la bandera 'x' (execute)."
    }
]


def load_reviews():
    if not os.path.exists(REVIEWS_FILE):
        return []
    with open(REVIEWS_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def save_review(entry):
    reviews = load_reviews()
    reviews.append(entry)
    with open(REVIEWS_FILE, "w", encoding="utf-8") as f:
        json.dump(reviews, f, indent=2, ensure_ascii=False)
    return reviews


def compute_badge(score, total, survived):
    ratio = score / total if total else 0
    if survived and ratio >= 0.85:
        return {
            "title": "PRINCIPAL SRE ARCHITECT",
            "icon": "🛡️",
            "color": "#00ff88",
            "desc": "Estabilizaste producción sin despeinarte. Deploy aprobado un viernes."
        }
    elif survived and ratio >= 0.5:
        return {
            "title": "SENIOR FIREFIGHTER",
            "icon": "🧯",
            "color": "#38bdf8",
            "desc": "Hubo humo y alertas rojas, pero el servidor sobrevivió a tu guardia."
        }
    elif survived:
        return {
            "title": "SURVIVOR POR MILAGRO",
            "icon": "🩹",
            "color": "#facc15",
            "desc": "El sistema corre con cinta adhesiva y fe, pero responde 200 OK."
        }
    else:
        return {
            "title": "CAUSANTE DEL KERNEL PANIC",
            "icon": "💀",
            "color": "#ff3355",
            "desc": "El datacenter ardió en llamas. Hora de actualizar el currículum."
        }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/questions")
def get_questions():
    """Selecciona preguntas al azar y mezcla el orden de sus opciones."""
    selected = random.sample(QUESTIONS, min(QUESTIONS_PER_GAME, len(QUESTIONS)))
    randomized = []
    for q in selected:
        indexed_opts = list(enumerate(q["options"]))
        random.shuffle(indexed_opts)
        new_options = [opt for _, opt in indexed_opts]
        new_correct = next(i for i, (orig_i, _) in enumerate(indexed_opts) if orig_i == q["correct"])
        randomized.append({
            "id": q["id"],
            "module": q["module"],
            "question": q["question"],
            "options": new_options,
            "correct": new_correct,
            "hint": q["hint"]
        })
    return jsonify(randomized)


@app.route("/api/submit-qa", methods=["POST"])
def submit_qa():
    data = request.get_json() or {}

    player = str(data.get("player_name", "")).strip() or "Dev_Anonimo"
    rating = data.get("rating")
    ux_feel = str(data.get("ux_feel", "")).strip()
    comment = str(data.get("comment", "")).strip()
    score = int(data.get("score", 0))
    total = int(data.get("total", QUESTIONS_PER_GAME))
    survived = bool(data.get("survived", False))
    final_temp = int(data.get("final_temp", 45))

    if not isinstance(rating, int) or rating < 1 or rating > 5:
        return jsonify({"error": "Debes seleccionar una calificación de 1 a 5 estrellas."}), 400
    if len(comment) < 5:
        return jsonify({"error": "Escribe un comentario breve de al menos 5 caracteres sobre tu experiencia."}), 400

    badge = compute_badge(score, total, survived)

    review_entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "player": player,
        "rating_stars": rating,
        "ux_perception": ux_feel,
        "comment": comment,
        "badge_title": badge["title"],
        "badge_icon": badge["icon"],
        "game_result": {
            "score": score,
            "total_questions": total,
            "survived": survived,
            "final_temp_c": final_temp
        }
    }

    all_reviews = save_review(review_entry)
    avg_rating = round(sum(r["rating_stars"] for r in all_reviews) / len(all_reviews), 2)

    return jsonify({
        "status": "signed_off",
        "badge": badge,
        "stats": {
            "total_reviews": len(all_reviews),
            "avg_rating": avg_rating
        }
    })


@app.route("/api/reviews")
def get_reviews():
    """Devuelve estadísticas globales y todos los registros de QA para la tabla."""
    reviews = load_reviews()
    total = len(reviews)
    avg = round(sum(r["rating_stars"] for r in reviews) / total, 2) if total else 0
    survived_count = sum(1 for r in reviews if r.get("game_result", {}).get("survived"))
    survival_rate = round((survived_count / total) * 100, 1) if total else 0

    return jsonify({
        "total_encuestados": total,
        "promedio_ux": avg,
        "tasa_supervivencia": survival_rate,
        "registros": list(reversed(reviews))  # Más recientes primero
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)