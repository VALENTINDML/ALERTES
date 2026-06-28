"""
Génération d'utilisateurs fictifs.

Ce script permet d'ajouter un nombre variable de faux utilisateurs
dans la base PostgreSQL, ainsi que leurs positions BTC/USDT et leurs
préférences d'alertes quotidiennes.

Il est relançable plusieurs fois : chaque exécution ajoute de nouveaux
utilisateurs sans modifier ceux déjà présents.
"""

import random
import sys
from datetime import datetime, timedelta

from faker import Faker
from psycopg2.extras import execute_values

from config.db import get_connection
from config.symbols import SYMBOLS


DEFAULT_TOTAL_USERS = 1000

REFERENCE_PRICES = {
    "BTC/USDT": 53477,
    "ETH/USDT": 2800,
    "SOL/USDT": 145,
    "BNB/USDT": 590,
    "XRP/USDT": 0.55,
    "ADA/USDT": 0.42,
    "DOGE/USDT": 0.12,
}

COUNTRIES = {
    "FR": {
        "country": "France",
        "locale": "fr_FR",
        "currency": "EUR",
        "language": "fr",
        "timezone": "Europe/Paris",
        "phone_code": "+33",
        "cities": [
            {"city": "Paris", "region": "Île-de-France", "postal_code": "75001"},
            {"city": "Marseille", "region": "Provence-Alpes-Côte d'Azur", "postal_code": "13001"},
            {"city": "Lyon", "region": "Auvergne-Rhône-Alpes", "postal_code": "69001"},
            {"city": "Toulouse", "region": "Occitanie", "postal_code": "31000"},
            {"city": "Nice", "region": "Provence-Alpes-Côte d'Azur", "postal_code": "06000"},
            {"city": "Nantes", "region": "Pays de la Loire", "postal_code": "44000"},
            {"city": "Strasbourg", "region": "Grand Est", "postal_code": "67000"},
            {"city": "Montpellier", "region": "Occitanie", "postal_code": "34000"},
            {"city": "Bordeaux", "region": "Nouvelle-Aquitaine", "postal_code": "33000"},
            {"city": "Lille", "region": "Hauts-de-France", "postal_code": "59000"},
        ],
    },
    "US": {
        "country": "United States",
        "locale": "en_US",
        "currency": "USD",
        "language": "en",
        "timezone": "America/New_York",
        "phone_code": "+1",
        "cities": [
            {"city": "New York", "region": "New York", "postal_code": "10001"},
            {"city": "Los Angeles", "region": "California", "postal_code": "90001"},
            {"city": "Chicago", "region": "Illinois", "postal_code": "60601"},
            {"city": "Houston", "region": "Texas", "postal_code": "77001"},
            {"city": "Phoenix", "region": "Arizona", "postal_code": "85001"},
            {"city": "Philadelphia", "region": "Pennsylvania", "postal_code": "19019"},
            {"city": "San Antonio", "region": "Texas", "postal_code": "78201"},
            {"city": "San Diego", "region": "California", "postal_code": "92101"},
            {"city": "Dallas", "region": "Texas", "postal_code": "75201"},
            {"city": "Miami", "region": "Florida", "postal_code": "33101"},     
        ],
    },
    "DE": {
        "country": "Germany",
        "locale": "de_DE",
        "currency": "EUR",
        "language": "de",
        "timezone": "Europe/Berlin",
        "phone_code": "+49",
        "cities": [
            {"city": "Berlin", "region": "Berlin", "postal_code": "10115"},
            {"city": "Hamburg", "region": "Hamburg", "postal_code": "20095"},
            {"city": "Munich", "region": "Bavaria", "postal_code": "80331"},
            {"city": "Cologne", "region": "North Rhine-Westphalia", "postal_code": "50667"},
            {"city": "Frankfurt", "region": "Hesse", "postal_code": "60311"},
            {"city": "Stuttgart", "region": "Baden-Württemberg", "postal_code": "70173"},
            {"city": "Düsseldorf", "region": "North Rhine-Westphalia", "postal_code": "40213"},
            {"city": "Leipzig", "region": "Saxony", "postal_code": "04109"},
            {"city": "Dortmund", "region": "North Rhine-Westphalia", "postal_code": "44135"},
            {"city": "Bremen", "region": "Bremen", "postal_code": "28195"},
        ],
    },
    "ES": {
        "country": "Spain",
        "locale": "es_ES",
        "currency": "EUR",
        "language": "es",
        "timezone": "Europe/Madrid",
        "phone_code": "+34",
        "cities": [
            {"city": "Madrid", "region": "Community of Madrid", "postal_code": "28001"},
            {"city": "Barcelona", "region": "Catalonia", "postal_code": "08001"},
            {"city": "Valencia", "region": "Valencian Community", "postal_code": "46001"},
            {"city": "Seville", "region": "Andalusia", "postal_code": "41001"},
            {"city": "Zaragoza", "region": "Aragon", "postal_code": "50001"},
            {"city": "Málaga", "region": "Andalusia", "postal_code": "29001"},
            {"city": "Murcia", "region": "Region of Murcia", "postal_code": "30001"},
            {"city": "Palma", "region": "Balearic Islands", "postal_code": "07001"},
            {"city": "Bilbao", "region": "Basque Country", "postal_code": "48001"},
            {"city": "Alicante", "region": "Valencian Community", "postal_code": "03001"},
        ],
    },
    "IT": {
        "country": "Italy",
        "locale": "it_IT",
        "currency": "EUR",
        "language": "it",
        "timezone": "Europe/Rome",
        "phone_code": "+39",
        "cities": [
            {"city": "Rome", "region": "Lazio", "postal_code": "00118"},
            {"city": "Milan", "region": "Lombardy", "postal_code": "20121"},
            {"city": "Naples", "region": "Campania", "postal_code": "80121"},
            {"city": "Turin", "region": "Piedmont", "postal_code": "10121"},
            {"city": "Palermo", "region": "Sicily", "postal_code": "90133"},
            {"city": "Genoa", "region": "Liguria", "postal_code": "16121"},
            {"city": "Bologna", "region": "Emilia-Romagna", "postal_code": "40121"},
            {"city": "Florence", "region": "Tuscany", "postal_code": "50121"},
            {"city": "Bari", "region": "Apulia", "postal_code": "70121"},
            {"city": "Catania", "region": "Sicily", "postal_code": "95121"},
        ],
    },
}

def generate_country_weights():
    """
    Génère une répartition aléatoire mais non uniforme des pays
    à chaque exécution du script.

    Exemple possible :
    FR = 78
    US = 42
    DE = 95
    ES = 31
    IT = 64

    Les pays restent choisis au hasard, mais certains auront
    plus de chances d'être sélectionnés que d'autres.
    """
    return {
        country_code: random.randint(20, 100)
        for country_code in COUNTRIES.keys()
    }

COUNTRY_WEIGHTS = generate_country_weights()

EMAIL_DOMAINS = [
    "gmail.com",
    "outlook.com",
    "hotmail.com",
    "yahoo.com",
]


def get_total_users_to_generate():
    if len(sys.argv) > 1:
        return int(sys.argv[1])

    return DEFAULT_TOTAL_USERS


def get_next_user_index():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT COALESCE(MAX(id), 0)
        FROM users;
    """)

    max_id = cur.fetchone()[0]

    cur.close()
    conn.close()

    return max_id + 1


def choose_country_code():
    """
    Choisit un pays au hasard avec une répartition aléatoire
    mais non uniforme.

    Les poids sont générés au lancement du script.
    """
    return random.choices(
        population=list(COUNTRY_WEIGHTS.keys()),
        weights=list(COUNTRY_WEIGHTS.values()),
        k=1,
    )[0]


def normalize_email(value):
    value = value.lower()
    value = value.replace(" ", "")
    value = value.replace("'", "")
    value = value.replace("’", "")

    replacements = {
        "é": "e",
        "è": "e",
        "ê": "e",
        "ë": "e",
        "à": "a",
        "â": "a",
        "ä": "a",
        "ù": "u",
        "û": "u",
        "ü": "u",
        "î": "i",
        "ï": "i",
        "ô": "o",
        "ö": "o",
        "ç": "c",
        "ñ": "n",
        "ß": "ss",
    }

    for source, target in replacements.items():
        value = value.replace(source, target)

    return value


def generate_phone(country_code, phone_code):
    digits = "".join(random.choice("0123456789") for _ in range(8))

    if country_code == "FR":
        return f"{phone_code} {random.choice(['6', '7'])} {digits[:2]} {digits[2:4]} {digits[4:6]} {digits[6:]}"

    if country_code == "US":
        return f"{phone_code} {digits[:3]}-{digits[3:6]}-{digits[6:]}"

    if country_code == "DE":
        return f"{phone_code} {digits[:3]} {digits[3:]}"

    if country_code == "ES":
        return f"{phone_code} {random.choice(['6', '7', '9'])}{digits[:2]} {digits[2:4]} {digits[4:6]} {digits[6:]}"

    if country_code == "IT":
        return f"{phone_code} {digits[:3]} {digits[3:]}"

    return f"{phone_code} {digits}"


def generate_users(total_users):
    start_index = get_next_user_index()
    end_index = start_index + total_users

    users = []

    for i in range(start_index, end_index):
        country_code = choose_country_code()
        country_data = COUNTRIES[country_code]
        city_data = random.choice(country_data["cities"])

        fake = Faker(country_data["locale"])

        first_name = fake.first_name()
        last_name = fake.last_name()

        email_domain = random.choice(EMAIL_DOMAINS)

        email = normalize_email(
            f"{first_name}.{last_name}.{i}@{email_domain}"
        )

        users.append(
            (
                email,
                first_name,
                last_name,
                True,
                country_code,
                country_data["country"],
                city_data["region"],
                city_data["city"],
                city_data["postal_code"],
                generate_phone(country_code, country_data["phone_code"]),
                country_data["phone_code"],
                country_data["currency"],
                country_data["language"],
                country_data["timezone"],
            )
        )

    return users


def save_users(users):
    """
    Insère les utilisateurs fictifs dans PostgreSQL.

    Returns:
        list[int]: IDs des utilisateurs réellement insérés.
    """
    conn = get_connection()
    cur = conn.cursor()

    inserted_rows = execute_values(
        cur,
        """
        INSERT INTO users (
            email,
            first_name,
            last_name,
            is_active,
            country_code,
            country,
            region,
            city,
            postal_code,
            phone,
            phone_code,
            currency,
            language,
            timezone
        )
        VALUES %s
        ON CONFLICT (email)
        DO NOTHING
        RETURNING id;
        """,
        users,
        fetch=True,
    )

    conn.commit()
    cur.close()
    conn.close()

    return [row[0] for row in inserted_rows]


def get_reference_price(symbol):
    """
    Retourne un prix de référence pour chaque crypto.

    Si le symbole n'est pas défini dans REFERENCE_PRICES,
    on utilise un prix par défaut pour éviter que le script plante.
    """
    return REFERENCE_PRICES.get(symbol, 100)


def get_total_positions_for_user():
    """
    Définit combien de cryptos différentes un utilisateur possède.

    La majorité des utilisateurs auront peu de positions.
    """
    return random.choices(
        [1, 2, 3, 4, 5],
        weights=[35, 30, 20, 10, 5],
    )[0]


def get_total_buys_for_symbol():
    """
    Définit combien d'achats différents existent pour une même crypto.

    Exemple :
    - un utilisateur peut avoir acheté BTC une seule fois ;
    - ou avoir acheté BTC plusieurs fois à des prix différents.
    """
    return random.choices(
        [1, 2, 3],
        weights=[70, 25, 5],
    )[0]


def generate_positions(user_ids):
    """
    Génère des positions crypto fictives.

    Logique :
    - chaque utilisateur possède plusieurs cryptos différentes ;
    - pour chaque crypto, il peut avoir un ou plusieurs achats ;
    - chaque achat devient une ligne dans user_positions ;
    - le prix d'achat dépend du symbole crypto.
    """
    conn = get_connection()
    cur = conn.cursor()

    positions = []

    max_symbols_per_user = min(5, len(SYMBOLS))

    for user_id in user_ids:
        total_symbols = min(
            get_total_positions_for_user(),
            max_symbols_per_user
        )

        user_symbols = random.sample(
            SYMBOLS,
            total_symbols
        )

        for symbol in user_symbols:
            total_buys = get_total_buys_for_symbol()
            reference_price = get_reference_price(symbol)

            for _ in range(total_buys):
                buy_price = reference_price * random.uniform(0.85, 1.15)

                quantity = round(random.uniform(0.01, 2.0), 4)

                buy_datetime = (
                    datetime.now()
                    - timedelta(days=random.randint(1, 180))
                )

                positions.append(
                    (
                        user_id,
                        symbol,
                        round(buy_price, 4),
                        quantity,
                        buy_datetime,
                        True,
                    )
                )

    if not positions:
        cur.close()
        conn.close()
        return

    execute_values(
        cur,
        """
        INSERT INTO user_positions (
            user_id,
            symbol,
            buy_price,
            quantity,
            buy_datetime,
            is_active
        )
        VALUES %s;
        """,
        positions,
    )

    conn.commit()
    cur.close()
    conn.close()


def generate_alert_preferences(user_ids):
    conn = get_connection()
    cur = conn.cursor()

    preferences = []

    for user_id in user_ids:
        for symbol in SYMBOLS:
            preferences.append(
                (
                    user_id,
                    symbol,
                    random.choice([True, False]),
                )
            )

    execute_values(
        cur,
        """
        INSERT INTO daily_alert_preferences (
            user_id,
            symbol,
            enabled
        )
        VALUES %s
        ON CONFLICT (user_id, symbol)
        DO NOTHING;
        """,
        preferences,
    )

    conn.commit()
    cur.close()
    conn.close()


def generate_price_alerts(user_ids):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            user_id,
            symbol,
            buy_price
        FROM user_positions
        WHERE user_id = ANY(%s)
          AND is_active = TRUE;
    """, (user_ids,))

    positions = cur.fetchall()

    price_alerts = []

    for user_id, symbol, buy_price in positions:
        direction = random.choice(["above", "below"])

        if direction == "above":
            multiplier = random.uniform(1.03, 1.15)
        else:
            multiplier = random.uniform(0.85, 0.97)

        target_price = round(buy_price * multiplier, 2)

        price_alerts.append(
            (
                user_id,
                symbol,
                target_price,
                direction,
                True,
            )
        )

    if price_alerts:
        execute_values(
            cur,
            """
            INSERT INTO price_alerts (
                user_id,
                symbol,
                target_price,
                direction,
                is_active
            )
            VALUES %s;
            """,
            price_alerts,
        )

    conn.commit()
    cur.close()
    conn.close()


def main():
    total_users = get_total_users_to_generate()

    print("Répartition aléatoire des pays :", COUNTRY_WEIGHTS)

    users = generate_users(total_users)

    new_user_ids = save_users(users)

    if not new_user_ids:
        print("Aucun nouvel utilisateur inséré.")
        return

    generate_positions(new_user_ids)

    generate_alert_preferences(new_user_ids)

    generate_price_alerts(new_user_ids)

    print(f"{len(new_user_ids)} nouveaux utilisateurs générés.")


if __name__ == "__main__":
    main()