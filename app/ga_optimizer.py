import random
from app.models import Subject

POPULATION_SIZE = 30
GENERATIONS = 30
MUTATION_RATE = 0.1

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri"]
PERIODS = [1, 2, 3, 4, 5]

YEARS = [
"MCA1","MCA2",
# "BCA1","BCA2","BCA3"
]
SECTIONS = ["A", "B"]


SEMESTER = "odd"   # odd / even

THEORY_ROOMS = ["T1","T2","T3","T4","T5","T6"]
LAB_ROOMS = ["LAB1","LAB2","LAB3"]

# ---------------- LOAD SUBJECTS FROM DATABASE ----------------
def get_subjects():

    subjects = []

    rows = Subject.query.all()

    for r in rows:

        # MCA odd-even
        if "MCA" in r.year:
            if SEMESTER == "odd" and r.year not in ["MCA1"]:
                continue
            if SEMESTER == "even" and r.year not in ["MCA2"]:
                continue

        # BCA odd-even
        # if "BCA" in r.year:
        #     if SEMESTER == "odd" and r.year not in ["BCA1","BCA3"]:
        #         continue
        #     if SEMESTER == "even" and r.year not in ["BCA2"]:
        #         continue

        subjects.append({
            "name": r.subject_name,
            "teacher": r.teacher,
            "type": r.subject_type,
            "hours": r.hours,
            "year": r.year,
            "section": r.section
        })

    return subjects


# ---------------- CREATE CHROMOSOME ----------------
def create_chromosome():

    chromosome = []
    subjects = get_subjects()

    for year in YEARS:
        for section in SECTIONS:

            used_slots = set()

            section_subjects = [
                s for s in subjects
                if s["year"] == year and s["section"] == section
            ]

            for sub in section_subjects:

                # LAB
                if sub["type"] == "lab":

                    placed = False
                    attempts = 0

                    while not placed and attempts < 50:

                        day = random.choice(DAYS)
                        start = random.choice([1, 2, 3, 4])

                        if (day, start) not in used_slots and (day, start+1) not in used_slots:

                            used_slots.add((day, start))
                            used_slots.add((day, start+1))

                            room = random.choice(LAB_ROOMS)

                            chromosome.append(
                                (day, start, year, section, sub["name"], sub["teacher"], "lab", room)
                            )

                            chromosome.append(
                                (day, start+1, year, section, sub["name"], sub["teacher"], "lab", room)
                            )

                            placed = True

                        attempts += 1

                # THEORY
                else:

                    for _ in range(sub["hours"]):

                        placed = False
                        attempts = 0

                        while not placed and attempts < 50:

                            day = random.choice(DAYS)
                            period = random.choice(PERIODS)

                            if (day, period) not in used_slots:

                                used_slots.add((day, period))

                                room = random.choice(THEORY_ROOMS)

                                chromosome.append(
                                    (day, period, year, section,
                                     sub["name"], sub["teacher"], "theory", room)
                                )

                                placed = True

                            attempts += 1

    return chromosome


# ---------------- FITNESS FUNCTION ----------------
def fitness(chromosome):

    score = 0

    class_slot_used = set()
    teacher_global_slot = set()
    room_slot = set()

    lab_count = {}
    theory_count = {}

    for d, p, y, sec, s, t, ty, room in chromosome:

        # class conflict
        if (d, p, y, sec) in class_slot_used:
            score -= 1000
        class_slot_used.add((d, p, y, sec))

        # teacher conflict
        if (d, p, t) in teacher_global_slot:
            score -= 1000
        teacher_global_slot.add((d, p, t))

        # room conflict
        if (d, p, room) in room_slot:
            score -= 1000
        room_slot.add((d, p, room))

        # classroom limit
        if ty == "lab":
            lab_count[(d, p)] = lab_count.get((d, p), 0) + 1
            if lab_count[(d, p)] > len(LAB_ROOMS):
                score -= 500

        else:
            theory_count[(d, p)] = theory_count.get((d, p), 0) + 1
            if theory_count[(d, p)] > len(THEORY_ROOMS):
                score -= 500

        # avoid last period theory
        if ty == "theory" and p == 5:
            score -= 2

    return score

# ---------------- CROSSOVER ----------------
def crossover(p1, p2):

    day = random.choice(DAYS)
    child = []

    for g1, g2 in zip(p1, p2):

        if g1[0] == day:
            child.append(g1)
        else:
            child.append(g2)

    return child


# ---------------- MUTATION ----------------
def mutate(chromosome):

    if random.random() < MUTATION_RATE:

        idxs = [i for i, g in enumerate(chromosome) if g[6] == "theory"]

        if idxs:

            i = random.choice(idxs)

            d, p, y, sec, s, t, ty, room = chromosome[i]

            chromosome[i] = (
                random.choice(DAYS),
                random.choice(PERIODS),
                y,
                sec,
                s,
                t,
                ty,
                random.choice(THEORY_ROOMS)
            )

    return chromosome

# ---------------- RUN GA ----------------
def run_ga():

    population = [create_chromosome() for _ in range(POPULATION_SIZE)]

    for gen in range(GENERATIONS):

        population.sort(key=fitness, reverse=True)

        if gen % 5 == 0:
            print("GEN", gen, "BEST FITNESS:", fitness(population[0]))

        elites = population[:8]
        next_gen = elites.copy()

        while len(next_gen) < POPULATION_SIZE:

            p1, p2 = random.sample(population[:20], 2)

            child = crossover(p1, p2)
            child = mutate(child)

            next_gen.append(child)

        population = next_gen

    return population[0]