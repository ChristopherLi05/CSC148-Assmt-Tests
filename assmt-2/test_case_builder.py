from __future__ import annotations

import threading
import random
from enum import Enum
import json
import os

from a1_entities import Person, Elevator
from a1_visualizer import Visualizer, WHITE, FPS, PersonSprite, ElevatorSprite, Direction, FLOOR_HEIGHT, _FloorSprite, WIDTH, _FloorNum, FLOOR_BORDER_HEIGHT

import tkinter as tk
import pygame


class EnhancedPerson(Person):
    def __init__(self, start: int, target: int, index):
        Person.__init__(self, start, target)

        self.index = index
        self.curr_elevator: Elevator | None = None
        self.waiting = True

    def __repr__(self) -> str:
        return f'Person(start={self.start}, target={self.target}, wait_time={self.wait_time}, elevator={self.curr_elevator})'

    def dump_data(self):
        # Returns start, target, wait_time, on_elevator
        return self.start, self.target, self.wait_time, self.curr_elevator is not None


class FloorNum(_FloorNum):
    def __init__(self, floor_y: int, text: str) -> None:
        _FloorNum.__init__(self, floor_y, text)
        self.f_num = int(text)


class State(Enum):
    ADD_PERSON_FROM_FLOOR = 0
    ADD_PERSON_TO_FLOOR = 1

    BOARD_ELEVATOR = 2


class Phase(Enum):
    DISEMBARK = 0
    ARRIVAL = 1
    BOARD = 2
    MOVE = 3


class ControlGrid(tk.Frame):
    AUTO_INCREASE_WAIT = False
    ENFORCE_PHASE = False
    AUTO_INCREASE_PHASE = False

    def __init__(self, master, visualizer: TestCaseVisualizer):
        tk.Frame.__init__(self, master)
        self.grid()

        self.master = master
        self.visualizer = visualizer

        self.phase = Phase.ARRIVAL

        self.people: list[EnhancedPerson] = []
        # self.people_buttons = []

        self.curr_state = None
        self.temp_data = None

        tk.Label(self, text="People").grid(row=0, column=0)

        tk.Button(self, text="Deselect", command=self.deselect_cb, width=15).grid(row=1, column=0)

        tk.Label(self, text="Elevators").grid(row=6, column=0)

        tk.Button(self, text="Deselect", command=self.deselect_cb, width=15).grid(row=7, column=0)

        for i, j in enumerate(self.visualizer.elevators):
            tk.Button(self, text=f"Elevator {i}", command=lambda x=(j, i): self.select_elevator_cb(*x), width=15).grid(row=7, column=i + 1)

        tk.Label(self, text="Floors").grid(row=8, column=0)

        for k in range(self.visualizer._num_floors):
            tk.Button(self, text=f"Floor {k + 1}", command=lambda x=k: self.select_floor_cb(x + 1), width=15).grid(row=9, column=k)

        tk.Label(self, text="Misc Widgets").grid(row=10, column=0)

        tk.Button(self, text="Increase Wait", command=self.increase_wait_cb, width=15).grid(row=11, column=0)
        tk.Button(self, text="Increase All Wait", command=self.increase_all_wait_cb, width=15).grid(row=11, column=1)
        tk.Button(self, text="Decrease Wait", command=self.decrease_wait_cb, width=15).grid(row=11, column=2)

        tk.Button(self, text="Board Elevator", command=self.board_elevator_cb, width=15).grid(row=12, column=0)
        tk.Button(self, text="Disembark Elevator", command=self.disembark_elevator_cb, width=15).grid(row=12, column=1)

        tk.Button(self, text="Move Elevator Up", command=self.elevator_going_up, width=15).grid(row=13, column=0)
        tk.Button(self, text="Move Elevator Down", command=self.elevator_going_down, width=15).grid(row=13, column=1)

        tk.Button(self, text="Add Person", command=self.add_person_cb, width=15).grid(row=14, column=0)
        tk.Button(self, text="Next Phase", command=self.next_phase_cb, width=15).grid(row=14, column=1)
        tk.Button(self, text="Next Round", command=self.next_round_cb, width=15).grid(row=14, column=2)

        tk.Button(self, text="Dump To File", command=self.dump_to_file, width=15).grid(row=15, column=0)

        # {
        #   "arrivals": {round_num: [(from, target)]}
        #   "rounds": {
        #       round_num: {
        #           "elevators": [(elevator_pos, [dump_data])]}
        #           "people": [dump_data]
        #       }
        #   }
        # }
        self.data = {"config": {
            "num_floors": self.visualizer._num_floors,
            "num_elevators": len(self.visualizer.elevators),
            "elevator_capacity": self.visualizer.elevators[0].capacity,
        }, "arrivals": {}, "rounds": {}}

    def clicked_sprites(self, sprites):
        for i in sprites:
            if isinstance(i, Elevator):
                elevator_num = self.visualizer.elevators.index(i)

                if self.curr_state == State.BOARD_ELEVATOR:
                    self.select_elevator_cb(i, elevator_num)
                # print(f"Elevator num: {elevator_num}")
            elif isinstance(i, FloorNum):
                self.select_floor_cb(i.f_num)
                # print(f"Floor num: {i.f_num}")

    def add_new_person(self, person):
        if ControlGrid.AUTO_INCREASE_PHASE and self.phase.value < Phase.ARRIVAL.value:
            self.phase = Phase.ARRIVAL

        if ControlGrid.ENFORCE_PHASE and self.phase != Phase.ARRIVAL:
            print("Not in correct phase")
            return

        self.people.append(person)
        tk.Button(self, text=f"Person {len(self.people)}", command=lambda: self.select_person_cb(person), width=15).grid(row=1, column=len(self.people))

        if self.visualizer.round_num not in self.data["arrivals"]:
            self.data["arrivals"][self.visualizer.round_num] = []
        self.data["arrivals"][self.visualizer.round_num].append((person.start, person.target))

        self.visualizer.show_arrivals({person.start: [person]})

    def add_person_cb(self):
        self.curr_state = State.ADD_PERSON_FROM_FLOOR
        print("Click the floor you would like the person to come from")

    def deselect_cb(self):
        self.curr_state = None
        self.visualizer.update_highlight(None)

    def select_person_cb(self, person):
        self.visualizer.update_highlight(person)
        self.curr_state = None

        print(f"Selected Person {person.index} : {person}")

    def increase_wait_cb(self):
        if self.visualizer.highlight_person is None:
            print("Select a person before doing this")
        else:
            self.visualizer.highlight_person.wait_time += 1
            self.visualizer.render()

    def decrease_wait_cb(self):
        if self.visualizer.highlight_person is None:
            print("Select a person before doing this")
        else:
            self.visualizer.highlight_person.wait_time -= 1
            self.visualizer.render_header(self.visualizer.round_num)

    def increase_all_wait_cb(self):
        for i in self.people:
            if i.waiting:
                i.wait_time += 1
        self.visualizer.render_header(self.visualizer.round_num)

    def next_phase_cb(self):
        self.next_phase()

    def next_phase(self, phase=None):
        if phase is None and self.phase is Phase.MOVE:
            self.next_round_cb()
            return

        self.phase = {
            -1: Phase.DISEMBARK,
            Phase.DISEMBARK: Phase.ARRIVAL,
            Phase.ARRIVAL: Phase.BOARD,
            Phase.BOARD: Phase.MOVE,
            Phase.MOVE: Phase.MOVE,
        }[phase or self.phase]

        print(f"Switch to phase {self.phase}")
        self.master.title(f"Control Panel - {self.phase}")

    def next_round_cb(self):
        if ControlGrid.AUTO_INCREASE_WAIT:
            self.increase_all_wait_cb()

        self.next_phase(-1)

        data = {
            "elevators": [],
            "people": []
        }

        for i in self.visualizer.elevators:
            data["elevators"].append([i.current_floor, [i.dump_data() for i in i.passengers]])

        for i in self.people:
            data["people"].append(i.dump_data())

        self.data["rounds"][self.visualizer.round_num] = data

        print(f"Saving Round {self.visualizer.round_num}")
        self.visualizer.next_round()

    def dump_to_file(self):
        os.makedirs("test_cases", exist_ok=True)

        with open(f"test_cases/test_case_{len(os.listdir('test_cases'))}.json", "w") as f:
            json.dump(self.data, f, indent=2)

    def board_elevator_cb(self):
        if ControlGrid.AUTO_INCREASE_PHASE and self.phase.value < Phase.BOARD.value:
            self.phase = Phase.BOARD

        if ControlGrid.ENFORCE_PHASE and self.phase != Phase.BOARD:
            print("Not in correct phase")
        elif self.visualizer.highlight_person is None:
            print("Select a person before doing this")
        else:
            p = self.visualizer.highlight_person
            if p.curr_elevator is None and p.waiting:
                self.curr_state = State.BOARD_ELEVATOR
                print("Click the elevator you would like the person to board")
            else:
                print("Person should be waiting for an elevator")

    def disembark_elevator_cb(self):
        if ControlGrid.AUTO_INCREASE_PHASE and self.phase.value < Phase.DISEMBARK.value:
            self.phase = Phase.DISEMBARK

        if ControlGrid.ENFORCE_PHASE and self.phase != Phase.DISEMBARK:
            print("Not in correct phase")
        elif self.visualizer.highlight_person is None:
            print("Select a person before doing this")
        else:
            e = self.visualizer.highlight_person.curr_elevator
            if e is not None:
                e.passengers.remove(self.visualizer.highlight_person)
                self.visualizer.highlight_person.curr_elevator = None
                self.visualizer.highlight_person.waiting = False
                self.visualizer.show_disembarking(self.visualizer.highlight_person, e)
            else:
                print("Select a person who is on an elevator first")

    def select_elevator_cb(self, elevator, elevator_num):
        if self.curr_state == State.BOARD_ELEVATOR:
            if self.visualizer.highlight_person is None:
                self.curr_state = None
                return

            p = self.visualizer.highlight_person

            if elevator.current_floor != p.start:
                print(f"Elevator must be in the same floor as the person")
                return
            self.curr_state = None

            print(f"Person {p.index} is boarding elevator {elevator_num}")

            p.curr_elevator = elevator
            elevator.passengers.append(p)

            self.visualizer.show_boarding(p, elevator)
        else:
            self.visualizer.update_highlight(elevator)

    def select_floor_cb(self, floor_num):
        if self.curr_state == State.ADD_PERSON_FROM_FLOOR:
            print(f"Person is arriving from floor {floor_num}, please click on the floor that they are going to.")

            self.curr_state = State.ADD_PERSON_TO_FLOOR
            self.temp_data = floor_num
        elif self.curr_state == State.ADD_PERSON_TO_FLOOR:
            if floor_num == self.temp_data:
                print(f"Person cannot be heading to the same floor that they came from. ")
            else:
                print(f"Person is going from floor {self.temp_data} to {floor_num}")

                p = EnhancedPerson(self.temp_data, floor_num, len(self.people) + 1)
                self.add_new_person(p)

                self.curr_state = None
                self.temp_data = None

    def elevator_going_up(self):
        if ControlGrid.AUTO_INCREASE_PHASE and self.phase.value < Phase.MOVE.value:
            self.phase = Phase.MOVE

        if ControlGrid.ENFORCE_PHASE and self.phase != Phase.MOVE:
            print("Not in correct phase")
        elif self.visualizer.highlight_elevator is None:
            print("Select an elevator first")
        elif self.visualizer.highlight_elevator.current_floor == self.visualizer._num_floors:
            print("Elevator is at its highest floor already")
        else:
            self.visualizer.highlight_elevator.current_floor += 1
            self.visualizer.show_elevator_moves([self.visualizer.highlight_elevator], [Direction.UP])

    def elevator_going_down(self):
        if ControlGrid.AUTO_INCREASE_PHASE and self.phase.value < Phase.MOVE.value:
            self.phase = Phase.MOVE

        if ControlGrid.ENFORCE_PHASE and self.phase != Phase.MOVE:
            print("Not in correct phase")
        elif self.visualizer.highlight_elevator is None:
            print("Select an elevator first")
        elif self.visualizer.highlight_elevator.current_floor == 1:
            print("Elevator is at its lowest floor already")
        else:
            self.visualizer.highlight_elevator.current_floor -= 1
            self.visualizer.show_elevator_moves([self.visualizer.highlight_elevator], [Direction.DOWN])

    @staticmethod
    def run(visualizer):
        threading.Thread(target=ControlGrid._run, args=(visualizer,), daemon=True).start()
        visualizer.run()

    @staticmethod
    def _run(visualizer: TestCaseVisualizer):
        root = tk.Tk()
        root.title("Control Panel")

        grid = ControlGrid(root, visualizer)

        visualizer.control_grid = grid

        grid.mainloop()


class TestCaseVisualizer(Visualizer):
    def __init__(self, elevators, num_floors):
        self.highlight_person: EnhancedPerson | None = None
        self.highlight_elevator: Elevator | None = None

        Visualizer.__init__(self, elevators, num_floors, True)

        self.elevators = elevators
        self.is_running = True
        self.round_num = 0

        self.update_render = True

        self.control_grid = None

    def run(self):
        while self.is_running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.is_running = False
                elif event.type == pygame.MOUSEBUTTONUP:
                    pos = pygame.mouse.get_pos()

                    clicked_sprites = [s for s in self._sprite_group if s.rect.collidepoint(pos)]
                    if self.control_grid:
                        self.control_grid.clicked_sprites(clicked_sprites)

            if self.update_render:
                self.update_render = False

                self.render_header(self.round_num)

    def update_highlight(self, thing: Elevator | Person | None):
        self.highlight_person = None
        self.highlight_elevator = None

        if isinstance(thing, Elevator):
            self.highlight_elevator = thing
        elif isinstance(thing, Person):
            self.highlight_person = thing

        self.update_render = True

    def render(self) -> None:
        """Draw the current state of the simulation to the screen.
        """
        if not self._visualize:
            return

        # Need this on OSX due to pygame bug
        pygame.event.peek(0)

        self._screen.fill(WHITE)

        if self.highlight_person is not None:
            pygame.draw.rect(self._screen, (255, 0, 0), self.highlight_person.rect)

        if self.highlight_elevator is not None:
            temp = self.highlight_elevator.rect

            pygame.draw.rect(self._screen, (255, 0, 0), pygame.Rect(temp.left - 5, temp.top - 5, temp.width + 10, temp.height + 10))

        self._sprite_group.draw(self._screen)
        self._stats_group.draw(self._screen)
        self._clock.tick(FPS)
        pygame.display.flip()

    def show_arrivals(self,
                      arrivals: dict[int, list[PersonSprite]]) -> None:
        """Show new arrivals."""
        x = 10
        for floor, people in arrivals.items():
            y = self._get_y_of_floor(floor)
            for person in people:
                person.rect.bottom = y
                person.rect.centerx = x + random.randint(-3, 3)
                self._sprite_group.add(person)
        self.render()

    def show_boarding(self, person: PersonSprite,
                      elevator: ElevatorSprite) -> None:
        target_x = elevator.rect.centerx + random.randint(-3, 3)
        person.rect.centerx = target_x

        elevator.update()
        self.render()

    def show_disembarking(self, person: PersonSprite,
                          elevator: ElevatorSprite) -> None:
        """Show disembarking of the given person from the given elevator."""
        target_x = WIDTH - 10

        elevator.update()
        person.rect.centerx = target_x

        # self._sprite_group.remove(person)
        self.render()

    def show_elevator_moves(self,
                            elevators: list[ElevatorSprite],
                            directions: list[Direction]) -> None:
        for elevator, direction in zip(elevators, directions):
            if direction == Direction.UP:
                step = - FLOOR_HEIGHT
            elif direction == Direction.DOWN:
                step = FLOOR_HEIGHT
            else:
                step = 0
            elevator.rect.bottom += step
            for passenger in elevator.passengers:
                passenger.rect.bottom += step

        self.render()

    def _setup_sprites(self, elevators: list[ElevatorSprite]) -> None:
        """Set up the initial sprites for this visualization.

        Position them on the screen and spaces them based on:
        - Size of the screen
        - Number of each item
        """
        for i, elevator in enumerate(elevators):
            elevator.rect.centerx = \
                (i + 1) * WIDTH // (self._num_elevators + 1)
            elevator.rect.bottom = self._total_height() - FLOOR_BORDER_HEIGHT

            self._sprite_group.add(elevator)

        for i in range(1, self._num_floors + 1):
            y = self._get_y_of_floor(i)
            floor = _FloorSprite(WIDTH, FLOOR_HEIGHT, y)
            floor_num = FloorNum(y - 20, str(i))
            self._sprite_group.add(floor_num)
            self._sprite_group.add(floor)

    def next_round(self):
        self.round_num += 1
        self.update_render = True


def main(num_floors_, num_elevators_, elevator_capacity_):
    v = TestCaseVisualizer([Elevator(elevator_capacity_) for _ in range(num_elevators_)], num_floors_)
    ControlGrid.run(v)


if __name__ == "__main__":
    # Auto increases wait time after each round
    ControlGrid.AUTO_INCREASE_WAIT = True
    # Enforces Phases
    ControlGrid.ENFORCE_PHASE = True
    # More Streamlined Phases
    ControlGrid.AUTO_INCREASE_PHASE = False

    num_floors = 5
    num_elevators = 1
    elevator_capacity = 2

    main(num_floors, num_elevators, elevator_capacity)
