"""
Nasta AS Kunde PoC - Mock Data Generator
Generates 50 Norwegian customers with machines and orders.
Distribution: ~15 low activity, ~20 medium, ~15 high activity.
Output: seed_data.sql
"""

import random
from datetime import date, timedelta
from faker import Faker

fake = Faker("no_NO")
random.seed(42)
Faker.seed(42)

# --- Configuration ---

MACHINE_MODELS = [
    ("Volvo EC220E Gravemaskin", 2015, 2024),
    ("Volvo EC350E Beltegraver", 2016, 2024),
    ("Volvo L120H Hjullaster", 2014, 2023),
    ("Volvo A30G Dumper", 2015, 2024),
    ("Caterpillar 320 Beltegraver", 2013, 2024),
    ("Caterpillar 950M Hjullaster", 2014, 2023),
    ("Caterpillar D6 Dozer", 2016, 2024),
    ("Caterpillar 745 Dumper", 2017, 2024),
    ("Komatsu PC210 Gravemaskin", 2012, 2023),
    ("Komatsu WA380 Hjullaster", 2015, 2024),
    ("Komatsu D65 Dozer", 2014, 2022),
    ("Liebherr R920 Gravemaskin", 2016, 2024),
    ("Liebherr LTM 1100 Mobilkran", 2018, 2024),
    ("Liebherr L566 Hjullaster", 2015, 2023),
    ("Hitachi ZX350 Beltegraver", 2013, 2023),
    ("Hitachi ZX210 Gravemaskin", 2014, 2024),
    ("JCB 3CX Lastemester", 2015, 2024),
    ("JCB 220X Gravemaskin", 2017, 2024),
    ("Doosan DX225 Gravemaskin", 2016, 2023),
    ("Hyundai HX300 Beltegraver", 2018, 2024),
    ("Takeuchi TB260 Minigraver", 2017, 2024),
    ("Kubota KX080 Minigraver", 2016, 2024),
    ("Atlas Copco FlexiROC Boremaskin", 2019, 2024),
    ("Sandvik DR410i Boremaskin", 2020, 2024),
    ("Epiroc SmartROC T40 Boremaskin", 2019, 2024),
]

ORDER_TYPES = ["Service", "Reparasjon", "Garanti", "Deler"]
ORDER_STATUSES = ["Mottatt", "Under behandling", "Ferdig", "Avsluttet"]

SYMPTOMS = [
    "Hydraulikklekkasje i hovedsylinder",
    "Motor starter ikke ved lave temperaturer",
    "Slitasje paa beltekjede",
    "Uvanlig stoey fra girkasse",
    "Oljetrykk-varsel paa dashboard",
    "Knekkledd har for mye slark",
    "Aircondition fungerer ikke",
    "Sprekk i frontrute",
    "Elektrisk feil i styringssystem",
    "Bremsesystem trenger justering",
    "Turbo gir lavere effekt enn normalt",
    "Kjoelesystem lekker",
    "Svinglager har unormal slitasje",
    "Eksosutslipp over tillatte verdier",
    "Styresylinder lekker olje",
    "Automatisk sentralsmoering virker ikke",
    "Grabbrotator reagerer tregt",
    "Hydraulikkpumpe gir redusert trykk",
    "Feilkode paa motorstyringsenheten",
    "Slitasje paa tenner paa skuffe",
    "Dieselfilter tett - hoeyt drivstofforbruk",
    "Hjullager paa venstre side slitt",
    "GPS/maskinstyring mister signal",
    "Vindusvisker defekt",
    "Setedemping slitt - vibrasjonsproblem",
    "Rust paa understellsramme",
    "Topplanpakning lekker",
    "Boomcylinder har intern lekkasje",
    "Joystick reagerer ujevnt",
    "Parkeringsbrems loesner ikke",
]

ORDER_DESCRIPTIONS = [
    "Aarlig service og vedlikehold",
    "Akutt reparasjon - maskin stoppet paa anlegg",
    "Garantireparasjon ihht. avtale",
    "Bestilling av slitedeler",
    "Planlagt 500-timers service",
    "Planlagt 1000-timers service",
    "Planlagt 2000-timers service",
    "Inspeksjon etter hendelse",
    "Oppgradering av maskinutstyr",
    "Utskifting av hydraulikkslanger",
    "Motoroverhaling",
    "Reparasjon etter transportskade",
    "Bytte av understellskomponenter",
    "Ettermontering av kamera/sensor",
    "Sesongklargjoring for vinterbruk",
]


def generate_org_nummer():
    """Generate realistic Norwegian org number (9 digits starting with 8 or 9)."""
    prefix = random.choice([8, 9])
    return f"{prefix}{random.randint(10000000, 99999999)}"


def generate_chassisnummer(machine_name: str, year: int) -> str:
    maker_codes = {
        "Volvo": "YV1",
        "Caterpillar": "CAT",
        "Komatsu": "KMT",
        "Liebherr": "LBH",
        "Hitachi": "HCM",
        "JCB": "JCB",
        "Doosan": "DSN",
        "Hyundai": "HYU",
        "Takeuchi": "TKC",
        "Kubota": "KBT",
        "Atlas Copco": "ATC",
        "Sandvik": "SVK",
        "Epiroc": "EPI",
    }
    maker = machine_name.split()[0]
    code = maker_codes.get(maker, "XXX")
    return f"{code}{year % 100}{random.randint(100000, 999999)}"


def main():
    customers = []
    machines = []
    orders = []

    used_org = set()
    used_chassis = set()
    order_counter = 10000

    # Activity distribution: 15 low, 20 medium, 15 high
    activity_levels = (
        [("low", 1, 1, 0, 1)] * 15
        + [("medium", 2, 4, 3, 8)] * 20
        + [("high", 5, 10, 10, 25)] * 15
    )
    random.shuffle(activity_levels)

    for i, (level, min_m, max_m, min_o, max_o) in enumerate(activity_levels):
        kundenummer = 1001 + i
        navn = fake.company()
        adresse = f"{fake.street_address()}, {fake.postcode()} {fake.city()}"
        epost = fake.company_email()
        telefonnummer = fake.phone_number()

        org = generate_org_nummer()
        while org in used_org:
            org = generate_org_nummer()
        used_org.add(org)

        customers.append((kundenummer, navn, adresse, epost, telefonnummer, org))

        num_machines = random.randint(min_m, max_m)
        customer_devices = []

        for j in range(num_machines):
            device_id = f"NAS-{kundenummer}-{j + 1:03d}"
            model_name, year_min, year_max = random.choice(MACHINE_MODELS)
            aarsmodell = random.randint(year_min, year_max)

            chassis = generate_chassisnummer(model_name, aarsmodell)
            while chassis in used_chassis:
                chassis = generate_chassisnummer(model_name, aarsmodell)
            used_chassis.add(chassis)

            machines.append(
                (kundenummer, device_id, model_name, aarsmodell, chassis)
            )
            customer_devices.append(device_id)

        num_orders = random.randint(min_o, max_o)
        for _ in range(num_orders):
            order_counter += 1
            ordrenummer = f"ORD-{order_counter}"
            ordretype = random.choice(ORDER_TYPES)
            beskrivelse = random.choice(ORDER_DESCRIPTIONS)
            device_id = random.choice(customer_devices)
            status = random.choice(ORDER_STATUSES)
            opprettet = date(2022, 1, 1) + timedelta(
                days=random.randint(0, 1190)
            )
            symptom = random.choice(SYMPTOMS) if ordretype != "Deler" else ""

            orders.append(
                (
                    kundenummer,
                    ordrenummer,
                    ordretype,
                    beskrivelse,
                    device_id,
                    status,
                    opprettet.isoformat(),
                    symptom,
                )
            )

    # Write seed_data.sql
    with open(
        "nasta-kunde-poc/data/seed_data.sql", "w", encoding="utf-8"
    ) as f:
        f.write("-- Nasta AS Kunde PoC - Seed Data\n")
        f.write(f"-- Generated: 50 customers, {len(machines)} machines, {len(orders)} orders\n\n")

        # Customers
        f.write("-- Customers\n")
        for c in customers:
            kn, navn, adr, ep, tlf, org = c
            navn_esc = navn.replace("'", "''")
            adr_esc = adr.replace("'", "''")
            f.write(
                f"INSERT INTO Customers (kundenummer, navn, adresse, epost, telefonnummer, org_nummer) "
                f"VALUES ({kn}, N'{navn_esc}', N'{adr_esc}', N'{ep}', N'{tlf}', N'{org}');\n"
            )

        f.write("\n-- Machines\n")
        for m in machines:
            kn, did, mn, yr, ch = m
            mn_esc = mn.replace("'", "''")
            f.write(
                f"INSERT INTO Machines (kundenummer, device_id, maskin_navn, aarsmodell, chassisnummer) "
                f"VALUES ({kn}, N'{did}', N'{mn_esc}', {yr}, N'{ch}');\n"
            )

        f.write("\n-- Orders\n")
        for o in orders:
            kn, onr, ot, besk, did, st, dato, sym = o
            besk_esc = besk.replace("'", "''")
            sym_esc = sym.replace("'", "''")
            f.write(
                f"INSERT INTO Orders (kundenummer, ordrenummer, ordretype, beskrivelse, device_id, status, opprettet_dato, symptomer_feil) "
                f"VALUES ({kn}, N'{onr}', N'{ot}', N'{besk_esc}', N'{did}', N'{st}', '{dato}', N'{sym_esc}');\n"
            )

    print(f"Generated seed_data.sql:")
    print(f"  Customers: {len(customers)}")
    print(f"  Machines:  {len(machines)}")
    print(f"  Orders:    {len(orders)}")


if __name__ == "__main__":
    main()
