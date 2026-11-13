from app import Sandbox


def main() -> None:
    app = Sandbox()
    feedback = app.run()
    print(feedback)


if __name__ == "__main__":
    main()
