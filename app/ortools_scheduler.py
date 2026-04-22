from ortools.sat.python import cp_model
from app.models import Subject

DAYS = ["Mon","Tue","Wed","Thu","Fri"]
PERIODS = [1,2,3,4,5]

THEORY_ROOMS = ["T1","T2","T3","T4","T5","T6"]
LAB_ROOMS = ["LAB1","LAB2","LAB3"]


def run_ortools():

    model = cp_model.CpModel()
    subjects = Subject.query.all()

    if not subjects:
        print("❌ No subjects found")
        return []

    slots = {}
    room_assign = {}
    timetable = []

    groups = set((s.year, s.semester, s.section) for s in subjects)

    # ---------------- VARIABLES ----------------
    for s in subjects:
        g = (s.year, s.semester, s.section)

        for d in range(5):
            for p in range(5):

                slots[(s.id, g, d, p)] = model.NewBoolVar(
                    f"slot_{s.id}_{d}_{p}"
                )

                room_list = THEORY_ROOMS if s.subject_type == "theory" else LAB_ROOMS

                for r in room_list:
                    room_assign[(s.id, g, d, p, r)] = model.NewBoolVar(
                        f"room_{s.id}_{d}_{p}_{r}"
                    )

    # ---------------- SUBJECT HOURS ----------------
    for s in subjects:
        g = (s.year, s.semester, s.section)

        model.Add(
            sum(slots[(s.id, g, d, p)]
                for d in range(5)
                for p in range(5)
            ) == s.hours
        )

    # ---------------- ONE SUBJECT PER SLOT ----------------
    for g in groups:
        for d in range(5):
            for p in range(5):

                model.Add(
                    sum(
                        slots[(s.id, g, d, p)]
                        for s in subjects
                        if (s.year, s.semester, s.section) == g
                    ) <= 1
                )

    # ---------------- TEACHER CLASH ----------------
    for d in range(5):
        for p in range(5):

            teachers = set(s.teacher for s in subjects)

            for t in teachers:
                model.Add(
                    sum(
                        slots[(s.id,(s.year,s.semester,s.section),d,p)]
                        for s in subjects
                        if s.teacher == t
                    ) <= 1
                )

    # ---------------- LAB CONSECUTIVE ----------------
    for s in subjects:
        if s.subject_type == "lab":

            g = (s.year, s.semester, s.section)

            pair_vars = {}

            for d in range(5):
                for p in range(4):
                    pair_vars[(d,p)] = model.NewBoolVar(f"labpair_{s.id}_{d}_{p}")

            # number of pairs
            model.Add(sum(pair_vars.values()) == s.hours // 2)

            for d in range(5):
                for p in range(5):

                    valid = []

                    if p > 0:
                        valid.append(pair_vars.get((d,p-1)))
                    if p < 4:
                        valid.append(pair_vars.get((d,p)))

                    valid = [v for v in valid if v is not None]

                    if valid:
                        for v in valid:
                            model.Add(slots[(s.id,g,d,p)] >= v)

                        model.Add(
                            slots[(s.id,g,d,p)] <= sum(valid)
                        )
                    else:
                        model.Add(slots[(s.id,g,d,p)] == 0)

    # ---------------- ROOM LINK ----------------
    for s in subjects:
        g = (s.year, s.semester, s.section)

        room_list = THEORY_ROOMS if s.subject_type == "theory" else LAB_ROOMS

        for d in range(5):
            for p in range(5):

                model.Add(
                    sum(room_assign[(s.id,g,d,p,r)] for r in room_list)
                    == slots[(s.id,g,d,p)]
                )

    # ---------------- ROOM CLASH ----------------
    for d in range(5):
        for p in range(5):

            for r in THEORY_ROOMS:
                model.Add(
                    sum(
                        room_assign[(s.id,(s.year,s.semester,s.section),d,p,r)]
                        for s in subjects if s.subject_type == "theory"
                    ) <= 1
                )

            for r in LAB_ROOMS:
                model.Add(
                    sum(
                        room_assign[(s.id,(s.year,s.semester,s.section),d,p,r)]
                        for s in subjects if s.subject_type == "lab"
                    ) <= 1
                )

    # ---------------- LAB SAME ROOM (FIXED) ----------------
    for s in subjects:
        if s.subject_type == "lab":

            g = (s.year, s.semester, s.section)

            for d in range(5):
                for p in range(4):

                    for r in LAB_ROOMS:
                        model.Add(
                            room_assign[(s.id,g,d,p,r)] ==
                            room_assign[(s.id,g,d,p+1,r)]
                        ).OnlyEnforceIf([
                            slots[(s.id,g,d,p)],
                            slots[(s.id,g,d,p+1)]
                        ])

    # ---------------- OBJECTIVE (IMPORTANT) ----------------
    model.Maximize(
        sum(slots.values())
    )

    # ---------------- SOLVE ----------------
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 10

    status = solver.Solve(model)

    print("STATUS:", status)

    if status not in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
        print("❌ NO SOLUTION")
        return []

    # ---------------- BUILD TIMETABLE ----------------
    for s in subjects:
        g = (s.year, s.semester, s.section)

        room_list = THEORY_ROOMS if s.subject_type == "theory" else LAB_ROOMS

        for d in range(5):
            for p in range(5):

                if solver.Value(slots[(s.id,g,d,p)]):

                    room = None
                    for r in room_list:
                        if solver.Value(room_assign[(s.id,g,d,p,r)]):
                            room = r
                            break

                    timetable.append((
                        DAYS[d],
                        PERIODS[p],
                        s.year,
                        s.semester,
                        s.section,
                        s.subject_name,
                        s.teacher,
                        s.subject_type,
                        room
                    ))

    print("TOTAL CLASSES:", len(timetable))

    return timetable