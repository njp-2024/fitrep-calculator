import sys
import os
from pathlib import Path
import numpy as np

# Ensure project root is in path
root_path = Path(__file__).resolve().parent.parent.parent
if str(root_path) not in sys.path:
    sys.path.append(str(root_path))

import src.app.models as models
import src.app.calc_eng as calc_eng
import src.app.constants as constants


class FitRepCLI:
    def __init__(self):
        # 1. Initialize Data Structures
        self.db = models.ReportDB()
        self.original_profile = None
        self.active_profile = None

        # 2. Load the Prompt Library (ExampleData) once at startup
        print("Loading data libraries...")
        self.example_data = models.ExampleData()

        self.running = True

    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def print_header(self):
        self.clear_screen()
        print("==========================================")
        print("      USMC FITREP CALCULATOR (CLI)        ")
        print("==========================================")
        if self.original_profile and self.active_profile:
            #print(self.original_profile)
            print(self.active_profile)
            # print(f"Current Profile: {self.profile.rank} | Reports: {self.db.get_num_reports()}")
            # print(f"Stats: High {self.profile.high:.2f} | Avg {self.profile.avg:.2f}")
        print("------------------------------------------")

    def setup_profile(self):
        """Initializes the RS Profile."""
        self.print_header()
        print("\n--- SETUP PROFILE ---")
        try:
            rank = input("Rank (e.g. Sgt, Capt): ").strip()
            high = float(input("Profile High (0-7): "))
            low = float(input("Profile Low (0-7): "))
            avg = float(input("Profile Avg (0-7): "))
            count = int(input("Total Reports (Before this session): "))

            self.original_profile = models.RankProfile("Original", rank, high, low, avg, count)
            self.active_profile = models.RankProfile("Active", rank, high, low, avg, count)
            print("\nProfile initialized successfully.")
            input("Press Enter to continue...")
        except ValueError:
            print("Invalid input. Please enter numbers for scores.")
            input("Press Enter to try again...")
            self.setup_profile()

    def _recalculate_all(self):
        """Helper to update all RVs based on the current profile state."""
        # Using the logic we centralized in calc_eng, specifically the helper function.
        # Accessing the 'private' helper because it does exactly what we need for the CLI state.
        calc_eng._update_profile(self.original_profile, self.active_profile, self.db)

    def add_report(self):
        """Adds a new Marine report."""
        if not self.original_profile or not self.active_profile:
            print("\n[!] Please set up a profile first.")
            input("Press Enter...")
            return

        self.print_header()
        print("\n--- ADD REPORT ---")
        name = input("MRO Name: ").strip().upper()
        if not name: return

        scores = {}
        print("\nEnter grades (A, B, C, D, E, F, G, H). 'H' is Not Observed.")

        for cat in constants.USMC_CATEGORIES:
            while True:
                grade = input(f"{cat}: ").strip().upper()
                if grade in constants.SCORE_LETTER_VALS:  #["A", "B", "C", "D", "E", "F", "G", "H"]:
                    scores[cat] = grade
                    break
                print("Invalid grade. Try again.")

        # Create Report using new Constructor
        new_rpt = models.Report(self.active_profile.rank, name, scores_dict=scores)

        # Add to DB
        self.db.add_report(new_rpt)

        # Update Calculations (Profile Stats + RVs)
        self._recalculate_all()

        print(f"\nSuccess! {name} added.")
        print(f"Report Avg: {new_rpt.rpt_avg:.2f}")
        print(f"RV (Proc):  {new_rpt.rv_proc:.2f}")
        print(f"RV (Cum):   {new_rpt.rv_cum:.2f}")
        input("Press Enter to continue...")

    def generate_narrative(self):
        """Uses the calc_eng LLM functions to draft text."""
        if not self.db.name_list:
            print("\n[!] No reports found.")
            input("Press Enter...")
            return

        self.print_header()
        print("\n--- GENERATE SECTION I ---")
        print("Available Marines:")
        for idx, name in enumerate(self.db.name_list):
            print(f"{idx + 1}. {name}")

        try:
            choice = int(input("\nSelect Marine # (0 to cancel): "))
            if choice == 0: return
            target_name = self.db.name_list[choice - 1]
        except (ValueError, IndexError):
            return

        report = self.db.get_report_by_name(target_name)

        # Input Context
        print(f"\nSelected: {target_name}")
        print("Enter Accomplishments (Press Enter twice to finish):")
        acc_lines = []
        while True:
            line = input()
            if not line: break
            acc_lines.append(line)
        report.accomplishments = "\n".join(acc_lines)

        print("\nEnter Context/Tone (Optional):")
        report.context = input()

        # Model Selection
        print("\nSelect Model:")
        print("1. Local (Mistral via Ollama)")
        print("2. Foundation (GPT-4o via OpenAI)")
        print("3. Open Weights (Qwen/Mixtral via HF)")

        m_choice = input("Choice: ").strip()

        print("\nGenerating... please wait...")

        result_text = ""
        model_name = ""

        # Pass 'self.example_data' to all query functions (Dependency Injection)
        if m_choice == "1":
            result_text, model_name = calc_eng.query_local(report, self.example_data)
        elif m_choice == "2":
            result_text, model_name = calc_eng.query_foundation(report, self.example_data)
        elif m_choice == "3":
            result_text, model_name = calc_eng.query_open(report, self.example_data)
        else:
            print("Invalid selection.")
            return

        # Display Result
        print(f"\n--- DRAFT ({model_name}) ---")
        print(result_text)
        print("-----------------------------")

        save = input("Save this text to report? (y/n): ").lower()
        if save == 'y':
            self.db.edit_report_sect_i(target_name, result_text)
            print("Saved.")
        input("Press Enter...")

    def show_summary(self):
        if not self.active_profile: return
        self.print_header()

        print(self.original_profile)
        print(self.active_profile)
        print("\nReports:")
        print(self.db)

        export = input("\nExport to file? (y/n): ").lower()
        if export == 'y':
            fname = "fitrep_export.txt"
            with open(fname, "w") as f:
                f.write(str(self.profile))
                f.write("\n\n")
                f.write(str(self.db))
            print(f"Exported to {fname}")
        input("Press Enter...")

    def run(self):
        while self.running:
            self.print_header()
            print("\n1. Setup/Edit Profile")
            print("2. Add Report")
            print("3. Generate Narratives")
            print("4. View Summary")
            print("5. Exit")

            choice = input("\nSelect Option: ").strip()

            if choice == "1":
                self.setup_profile()
            elif choice == "2":
                self.add_report()
            elif choice == "3":
                self.generate_narrative()
            elif choice == "4":
                self.show_summary()
            elif choice == "5":
                self.running = False
            else:
                pass


if __name__ == "__main__":
    app = FitRepCLI()
    app.run()



# import sys
# import os
# from pathlib import Path
#
# # Ensure project root is in path
# root_path = Path(__file__).resolve().parent.parent
# if str(root_path) not in sys.path:
#     sys.path.append(str(root_path))
#
# import src.app.models as models
# import src.app.calc_eng as calc_eng
# import src.app.constants as constants
#
# class FitRepCLI:
#     def __init__(self):
#         self.db = models.ReportDB()
#         self.profile = None
#         self.running = True
#
#     def clear_screen(self):
#         os.system('cls' if os.name == 'nt' else 'clear')
#
#     def print_header(self):
#         self.clear_screen()
#         print("==========================================")
#         print("      USMC FITREP CALCULATOR (CLI)        ")
#         print("==========================================")
#         if self.profile:
#             print(f"Current Profile: {self.profile.rank} | Reports: {self.db.get_num_reports()}")
#             print(f"Stats: High {self.profile.high:.2f} | Avg {self.profile.avg:.2f}")
#         print("------------------------------------------")
#
#     def setup_profile(self):
#         """Initializes the RS Profile."""
#         self.print_header()
#         print("\n--- SETUP PROFILE ---")
#         try:
#             rank = input("Rank (e.g. Sgt, Capt): ").strip()
#             high = float(input("Profile High (0-7): "))
#             low = float(input("Profile Low (0-7): "))
#             avg = float(input("Profile Avg (0-7): "))
#             count = int(input("Total Reports: "))
#
#             self.profile = models.RankProfile("Active", rank, high, low, avg, count)
#             print("\nProfile initialized successfully.")
#             input("Press Enter to continue...")
#         except ValueError:
#             print("Invalid input. Please enter numbers for scores.")
#             input("Press Enter to try again...")
#             self.setup_profile()
#
#     def add_report(self):
#         """Adds a new Marine report."""
#         if not self.profile:
#             print("\n[!] Please set up a profile first.")
#             input("Press Enter...")
#             return
#
#         self.print_header()
#         print("\n--- ADD REPORT ---")
#         name = input("MRO Name: ").strip().upper()
#         if not name: return
#
#         scores = {}
#         print("\nEnter grades (A, B, C, D, E, F, G, H). 'H' is Not Observed.")
#
#         for cat in constants.USMC_CATEGORIES:
#             while True:
#                 grade = input(f"{cat}: ").strip().upper()
#                 if grade in ["A", "B", "C", "D", "E", "F", "G", "H"]:
#                     scores[cat] = grade
#                     break
#                 print("Invalid grade. Try again.")
#
#         # Validation using calc_eng
#         msg, is_valid = calc_eng.validate_rpt_inputs(name, scores)
#         if not is_valid:
#             print(f"\n[!] Error: {msg}")
#             input("Press Enter...")
#             return
#
#         # Create and Save Report
#         # Note: We interact with models directly here since CLI is persistent
#         new_rpt = models.Report(self.profile.rank, name)
#         new_rpt.set_scores_with_dict(scores)
#         self.db.add_report(new_rpt)
#
#         # Update Calculations
#         self.profile.update(self.db)
#         self.db.update_rvs(self.profile)
#
#         print(f"\nSuccess! {name} added.")
#         print(f"Report Avg: {new_rpt.rpt_avg:.2f}")
#         print(f"RV (Proc):  {new_rpt.rv_proc:.2f}")
#         input("Press Enter to continue...")
#
#     def generate_narrative(self):
#         """Uses the calc_eng LLM functions to draft text."""
#         if not self.db.name_list:
#             print("\n[!] No reports found.")
#             input("Press Enter...")
#             return
#
#         self.print_header()
#         print("\n--- GENERATE SECTION I ---")
#         print("Available Marines:")
#         for idx, name in enumerate(self.db.name_list):
#             print(f"{idx + 1}. {name}")
#
#         try:
#             choice = int(input("\nSelect Marine # (0 to cancel): "))
#             if choice == 0: return
#             target_name = self.db.name_list[choice - 1]
#         except (ValueError, IndexError):
#             return
#
#         report = self.db.get_report_by_name(target_name)
#
#         # Input Context
#         print(f"\nSelected: {target_name}")
#         print("Enter Accomplishments (Press Enter twice to finish):")
#         acc_lines = []
#         while True:
#             line = input()
#             if not line: break
#             acc_lines.append(line)
#         report.accomplishments = "\n".join(acc_lines)
#
#         print("\nEnter Context/Tone (Optional):")
#         report.context = input()
#
#         # Model Selection
#         print("\nSelect Model:")
#         print("1. Local (Mistral via Ollama)")
#         print("2. Cloud (GPT-4o via OpenAI)")
#         print("3. Manual Entry")
#
#         m_choice = input("Choice: ").strip()
#
#         print("\nGenerating... please wait...")
#
#         result_text = ""
#         model_name = ""
#
#         if m_choice == "1":
#             # Using the calc_eng wrapper which handles clients/paths
#             result_text, model_name = calc_eng.query_local(report)
#         elif m_choice == "2":
#             result_text, model_name = calc_eng.query_foundation(report)
#         else:
#             result_text, model_name = calc_eng.query_manual()
#
#         # Display Result
#         print(f"\n--- DRAFT ({model_name}) ---")
#         print(result_text)
#         print("-----------------------------")
#
#         save = input("Save this text to report? (y/n): ").lower()
#         if save == 'y':
#             self.db.edit_report_sect_i(target_name, result_text)
#             print("Saved.")
#         input("Press Enter...")
#
#     def show_summary(self):
#         if not self.profile: return
#         self.print_header()
#         # reusing the helper from calc_eng
#         summary = calc_eng.print_profile(self.db, self.profile)
#         print(summary)
#
#         export = input("\nExport to file? (y/n): ").lower()
#         if export == 'y':
#             fname = "fitrep_export.txt"
#             with open(fname, "w") as f:
#                 f.write(summary)
#             print(f"Exported to {fname}")
#         input("Press Enter...")
#
#     def run(self):
#         while self.running:
#             self.print_header()
#             print("\n1. Setup/Edit Profile")
#             print("2. Add Report")
#             print("3. Generate Narratives")
#             print("4. View Summary")
#             print("5. Exit")
#
#             choice = input("\nSelect Option: ").strip()
#
#             if choice == "1":
#                 self.setup_profile()
#             elif choice == "2":
#                 self.add_report()
#             elif choice == "3":
#                 self.generate_narrative()
#             elif choice == "4":
#                 self.show_summary()
#             elif choice == "5":
#                 self.running = False
#             else:
#                 pass
#
#
# if __name__ == "__main__":
#     app = FitRepCLI()
#     app.run()
