# CSC148 - Assignment 1 Test Case Builder

This is a tool that I created for myself to test my assignment 1 algorithms. This was written in roughly 2 hours without any planning so it's extremely messy. I also haven't done many typings so :p

An example test case has been provided for you in `test_cases/test_case_0.json`

---

## How to Run

1. Copy and paste `test_case_builder.py` and `test_case_tester.py` into the assignments 1 folder.
2. Look in `test_case_builder.py` and locate `if __name__ == "__main__"`
   - Edit  `num_floors`, `num_elevators`, `elevator_capacity` to get your desired amount of floors
3. Run `test_case_builder.py` and manually do simulations out
   - To add a person: click `Add Person` and then you desired floors
   - To make a person board an elevator: click `Person #` button, click `Board Elevator` and click `Elevator #`
   - TO make a person disembark an elevator: click `Person #` button, clicking `Disembark Elevator`
   - `Next/Previous Phase` is important! If you have `ControlGrid.ENFORCE_PHASE = True` you will need to increment the phase in order to do more things
   - `Next Round` will save the round state to memory
   - `Dump To File` will dump the entire simulation to a file on disk
4. Edit `test_case_tester.py` and setup everything correctly
   - Locate `if __name__ == "__main__":` line
   - Add a `test_simulation("test_cases/test_case_##.json", SimulationAlgorithm())` and replace the file path and algorithm
5. Run the file and look into console to see what differs
