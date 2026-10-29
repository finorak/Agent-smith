from time import sleep

from .utils import basic_error_handler


@basic_error_handler
def main():
    print("Hello from agent-smith!")
    sleep(5)


if __name__ == "__main__":
    main()
