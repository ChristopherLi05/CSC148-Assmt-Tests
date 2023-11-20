from a1_entities import Person
from a1_simulation import Simulation
from a1_algorithms import ArrivalGenerator, EndToEndLoop, FurthestFloor

import json


class TestCaseGenerator(ArrivalGenerator):
    def __init__(self, arrivals):
        super().__init__(2)

        self.arrivals = arrivals
        self.arrived_people = []

    def generate(self, round_num: int) -> dict[int, list[Person]]:
        if str(round_num) not in self.arrivals:
            return {}
        else:
            data_ = {}

            for i in self.arrivals[str(round_num)]:
                if i[0] not in data_:
                    data_[i[0]] = []

                p = Person(*i)
                data_[i[0]].append(p)
                self.arrived_people.append(p)

            return data_


def dump_person_data(person, ppl_in_elvt):
    return [person.start, person.target, person.wait_time, person in ppl_in_elvt]


def dump_elevator_data(elevator, ppl_in_elvt):
    return [elevator.current_floor, [dump_person_data(p, ppl_in_elvt) for p in elevator.passengers]]


def run_sim(sim, round_num):
    sim.visualizer.render_header(round_num)

    # Stage 1: elevator disembarking
    sim.handle_disembarking()

    # Stage 2: new arrivals
    sim.generate_arrivals(round_num)

    # Stage 3: elevator boarding
    sim.handle_boarding()

    # Stage 4: move the elevators
    sim.move_elevators()

    # Stage 5: update wait times
    sim.update_wait_times()


def test_simulation(test_case_path, moving_algorithm):
    with open(test_case_path) as f:
        data = json.load(f)

    gen = TestCaseGenerator(data["arrivals"])

    config = data["config"]
    config["arrival_generator"] = gen
    config["moving_algorithm"] = moving_algorithm
    config["visualize"] = False

    s = Simulation(config)

    for rn, round_ in data["rounds"].items():
        # The test cases only dump data after the simulation is done
        run_sim(s, int(rn))

        ppl_in_elvt = []
        for j in s.elevators:
            ppl_in_elvt += j.passengers

        # Checking elevators
        for i, (e1, e2) in enumerate(zip(round_["elevators"], s.elevators)):
            if e1 != dump_elevator_data(e2, ppl_in_elvt):
                print(
                    f"Error in round {rn} for test case `{test_case_path}`: Elevator {i} did not match")
                print(e1, dump_elevator_data(e2, ppl_in_elvt))

                s.visualizer.wait_for_exit()
                return

        # Checking passengers
        for i, (p1, p2) in enumerate(zip(round_["people"], gen.arrived_people)):
            if p1 != dump_person_data(p2, ppl_in_elvt):
                print(
                    f"Error in round {rn} for test case `{test_case_path}`: Elevator {i} did not match")
                print(p1, dump_elevator_data(p2, ppl_in_elvt))

                s.visualizer.wait_for_exit()
                return

    print(f"The simulation passes `{test_case_path}`")


if __name__ == "__main__":
    test_simulation("test_cases/test_case_0.json", FurthestFloor())
    test_simulation("test_cases/test_case_1.json", EndToEndLoop())
    test_simulation("test_cases/test_case_2.json", FurthestFloor())
    test_simulation("test_cases/test_case_3.json", FurthestFloor())
