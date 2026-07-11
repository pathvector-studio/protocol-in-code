from protocol_in_code.stp.blocking import Bpdu
from protocol_in_code.stp.port_roles import PortRole, PortView, assign_roles
from protocol_in_code.stp.root_election import BridgeId


def main() -> None:
    print("Session 03 walkthrough: Ports have roles")
    print()

    root = BridgeId(priority=100, mac="00:00:00:00:00:0a")
    us = BridgeId(priority=32768, mac="00:00:00:00:00:0b")
    other_speaker = BridgeId(priority=32768, mac="00:00:00:00:00:0c")

    # --- The root bridge: every port is DESIGNATED, no exceptions ---
    root_offer_1 = Bpdu(root_id=root, root_path_cost=0, sender_bridge=root, sender_port=1)
    root_offer_2 = Bpdu(root_id=root, root_path_cost=0, sender_bridge=root, sender_port=2)
    root_ports = (
        PortView(port_id=1, heard=None, my_offer=root_offer_1),
        PortView(port_id=2, heard=None, my_offer=root_offer_2),
    )
    root_roles = assign_roles(root_ports, i_am_root=True)
    marker = "OK" if all(role is PortRole.DESIGNATED for role in root_roles.values()) else "NG"
    role_names = [role.value for role in root_roles.values()]
    print(f"[{marker}] root bridge: every port DESIGNATED  -> roles={role_names}")

    # --- A non-root with two ports: exactly one ROOT_PORT (the cheaper offer) ---
    cheap_offer = Bpdu(root_id=root, root_path_cost=19, sender_bridge=us, sender_port=1)
    expensive_offer = Bpdu(root_id=root, root_path_cost=100, sender_bridge=us, sender_port=2)
    two_ports = (
        PortView(port_id=1, heard=None, my_offer=cheap_offer),
        PortView(port_id=2, heard=None, my_offer=expensive_offer),
    )
    two_port_roles = assign_roles(two_ports, i_am_root=False)
    root_port_count = sum(1 for role in two_port_roles.values() if role is PortRole.ROOT_PORT)
    marker = "OK" if root_port_count == 1 and two_port_roles[1] is PortRole.ROOT_PORT else "NG"
    role_names = {port_id: role.value for port_id, role in two_port_roles.items()}
    print(f"[{marker}] non-root, two ports: exactly one ROOT_PORT -> count={root_port_count} roles={role_names}")

    # --- A port hearing a superior offer (better root_path_cost) than ours goes BLOCKED ---
    our_offer_on_segment = Bpdu(root_id=root, root_path_cost=19, sender_bridge=us, sender_port=3)
    superior_heard = Bpdu(root_id=root, root_path_cost=4, sender_bridge=other_speaker, sender_port=1)
    blocked_ports = (
        PortView(port_id=1, heard=None, my_offer=cheap_offer),
        PortView(port_id=3, heard=superior_heard, my_offer=our_offer_on_segment),
    )
    blocked_roles = assign_roles(blocked_ports, i_am_root=False)
    marker = "OK" if blocked_roles[3] is PortRole.BLOCKED else "NG"
    print(f"[{marker}] port hearing a superior offer -> BLOCKED   -> role={blocked_roles[3].value}")

    # --- A port hearing nothing (heard=None) cannot be blocked, so it's DESIGNATED ---
    silent_port = PortView(port_id=4, heard=None, my_offer=our_offer_on_segment)
    silent_ports = (
        PortView(port_id=1, heard=None, my_offer=cheap_offer),
        silent_port,
    )
    silent_roles = assign_roles(silent_ports, i_am_root=False)
    marker = "OK" if silent_roles[4] is PortRole.DESIGNATED else "NG"
    print(f"[{marker}] port hearing nothing -> DESIGNATED         -> role={silent_roles[4].value}")


if __name__ == "__main__":
    main()
