from protocol_in_code.ospf.dr_election import InterfaceCandidate, elect_dr_bdr


def main() -> None:
    result = elect_dr_bdr(
        (
            InterfaceCandidate(router_id="1.1.1.1", priority=1),
            InterfaceCandidate(router_id="2.2.2.2", priority=100, declared_dr=True),
            InterfaceCandidate(router_id="3.3.3.3", priority=50, declared_bdr=True),
            InterfaceCandidate(router_id="4.4.4.4", priority=0),
        )
    )

    print("dr:", result.designated_router)
    print("bdr:", result.backup_designated_router)
    print("eligible:", result.eligible_routers)


if __name__ == "__main__":
    main()

