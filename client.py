from cli_game import GameClient

if __name__ == "__main__":
    try:
        GameClient().run()
    except KeyboardInterrupt:
        print("\nКлиент завершён.")
