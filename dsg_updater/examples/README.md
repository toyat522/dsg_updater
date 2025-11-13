# Example usage for DSG Updater

1. Run `cypher_update_robot_state.py` to create or update robot state

```
python cypher_update_robot_state.py --robot hamilton --x 1.0 --y 1.0
```

2. Run `cypher_get_obj_center.py` to check the current object location (e.g. O43 is a bag)

```
python cypher_get_obj_center.py --object O43
```

3. Run `cypher_toggle_hold_state.py` for the robot to hold the bag (rerun to "unhold")

```
python cypher_toggle_hold_state.py --robot hamilton --object O43
```

4. Run `cypher_get_robot_state.py` to confirm the updated robot state in the Heracles DB

```
python cypher_get_robot_state.py --robot hamilton
```

5. Run `update_robot_holding_object_state.py` to continuously update the object position to match the robot position

```
python update_robot_holding_object_state.py
```
