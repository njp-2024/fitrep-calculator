import numpy as np
import yaml
from pathlib import Path

import src.app.constants as constants

####################################################################################
################################  Report class #####################################
####################################################################################
class Report:
    """
    Represents a single Marine's Fitness Report (FitRep).

    Holds the scores, calculated averages (RV), and narrative text inputs.
    """
    def __init__(self, rank, name, scores_dict=None):
        """
        Args:
            rank (str): The rank of the Marine (e.g., "Capt").
            name (str): The last name of the Marine.
            scores_dict (dict, optional): Dictionary of 14 attributes mapped to letter grades (A-H).
        """
        self.rank = rank
        self.name = name
        self.scores_dict = scores_dict if scores_dict is not None else {}
        # values
        self.scores = np.zeros(14)
        self.rpt_avg = 0
        # min/max rvs
        self.rv_proc_min = 0
        self.rv_cum_min = 0
        self.rv_proc_max = 0
        self.rv_cum_max = 0
        # narratives
        self.prompt = {"system": "Please enter accomplishments to generate a prompt",
                       "user" : "Please enter accomplishments to generate a prompt"
                       }
        self.billet = ""
        self.accomplishments = ""
        self.context = ""
        self.secti = ""
        self.secti_gens = 0
        self.last_gen_hash = None
        # if scores are provided, then update the values
        if scores_dict is not None:
            self.set_scores_with_dict(scores_dict)
            self._calc_rpt_avg()

    def get_letter_scores(self):
        """Returns the raw dictionary of letter grades."""
        return self.scores_dict

    def _calc_rpt_avg(self):
        """
        Calculates the report average, ignoring 'H' (Not Observed) values.
        'H' values are stored as 0 in self.scores.
        """
        keep_vals = self.scores != 0
        if np.any(keep_vals):
            self.rpt_avg = self.scores[keep_vals].mean()
        else:
            self.rpt_avg = 0

    def _assign_score(self, score_char):
        """
        Returns the appropriate value for the letter score.
        A=1, G=7, H=0 (Not Observed).
        Returns -1 for invalid letters.
        """
        return constants.SCORE_MAP.get(score_char, -1)

    def set_scores_with_dict(self, score_dict):
        """
        Parses a dictionary of attributes and updates the internal numpy array.
        """
        for i, key in enumerate(constants.USMC_CATEGORIES):
            if key in score_dict:
                self.scores[i] = self._assign_score(score_dict[key])

    def scores_as_str(self):
        """
        Formats scores into the standard FitRep visual block string.
        Example: "CC CCC CCCCC CCC H"
        """
        letters = list(self.get_letter_scores().values())
        if len(letters) < 14:
            return "Incomplete Scores"
        res_str = (f"{"".join(letters[0:2])} "      # Mission
                   f"{"".join(letters[2:5])} "      # Character
                   f"{"".join(letters[5:10])} "     # Leadership
                   f"{"".join(letters[10:13])} "    # Intellect
                   f"{letters[13]}")                # Reports
        return res_str

    def print_prompt(self):
        return f"""### INSTRUCTIONS ###
{self.prompt["system"]}

### DATA AND CONTEXT ###
{self.prompt["user"]}
"""

    def __repr__(self):
        res_str = f"**********************************\n"
        res_str += f"{self.rank} {self.name}:\n"
        res_str += f"Rpt Avg:   {self.rpt_avg:.2f}\n"
        res_str += f"RV Proc:   {self.rv_proc_min:.2f} - {self.rv_proc_max:.2f}\n"
        res_str += f"RV Cum:    {self.rv_cum_min:.2f} - {self.rv_cum_max:.2f}\n"
        res_str += f"Scores:    {self.scores_as_str()}\n"
        res_str += f"Billet:    {self.billet}\n"
        res_str += f"Accomplishments:\n"
        res_str += f"{self.accomplishments}\n\n"
        res_str += f"Sect I:\n"
        res_str += f"{self.secti}\n\n"
        res_str += f"Prompt:\n"
        res_str += f"--------------------------\n"
        res_str += self.print_prompt()
        res_str += f"--------------------------\n"
        res_str += f"**********************************"
        return res_str


####################################################################################
#################################  Rank Profile ####################################
####################################################################################

class RankProfile:
    """
    Tracks statistical profile for a specific rank (e.g., Captains).
    Used to calculate Relative Value (RV).
    """
    def __init__(self, label, rank, high, low, avg, num_rpts):
        self.label = label
        self.rank = rank
        self.high = high
        self.low = low
        self.avg = avg
        self.low_avg = avg - 0.005
        self.high_avg = avg + 0.005     # accounts for precision loss
        self.num_rpts = num_rpts

        # new value, attempt to reduce prrecision errors
        self.score_sum = avg * num_rpts

    def set_values(self, high, low, avg, num_rpts):
        self.high = high
        self.low = low
        self.avg = avg
        self.low_avg = avg - 0.005
        self.high_avg = avg + 0.005  # accounts for precision loss
        self.num_rpts = num_rpts
        self.score_sum = avg * num_rpts

    def update_with_rpt(self, rpt):
        """
        Updates the running average, high, and low based on a new report.
        """
        if rpt.rpt_avg > self.high:
            self.high = rpt.rpt_avg

        if rpt.rpt_avg < self.low or self.low == 0:
            self.low = rpt.rpt_avg

        score_sum = self.avg * self.num_rpts
        score_sum += rpt.rpt_avg
        self.num_rpts += 1
        #self.avg = score_sum / self.num_rpts
        # welfords
        self.avg = self.avg + ((rpt.rpt_avg - self.avg) / self.num_rpts)
        self.low_avg = self.low_avg + ((rpt.rpt_avg - self.low_avg) / self.num_rpts)
        self.high_avg = self.high_avg + ((rpt.rpt_avg - self.high_avg) / self.num_rpts)

        # new
        self.score_sum += rpt.rpt_avg

    def get_average(self):
        """
        added to reduce precision errors caused by rounded profile averages
        :return:
        """
        return self.score_sum / self.num_rpts

    def __repr__(self):
        res_str = f"{self.label} {self.rank} Profile - {self.num_rpts} Reports\n"
        res_str += f"     High:  {self.high:.2f}\n"
        res_str += f"     Low: {self.low:.2f}\n"
        res_str += f"     Avg: {self.avg:.2f}\n"
        return res_str

####################################################################################
##################################  Rpt DB #########################################
####################################################################################
# store reports entered by user.
class ReportDB:
    """
    In-memory database to store current session reports.
    Maintains insertion order using a list + dict approach.
    """
    def __init__(self):
        self.name_list = []
        self.rpts_dict = {}

    def add_report(self, new_rpt):
        """Adds a new report. If name exists, duplicates are not handled (overwrites dict key)."""
        if new_rpt.name not in self.rpts_dict:
            self.name_list.append(new_rpt.name)
        self.rpts_dict[new_rpt.name] = new_rpt

    def replace_rpt(self, new_rpt):
        """Updates an existing report object."""
        self.rpts_dict[new_rpt.name] = new_rpt

    def edit_report_sect_i(self, name, final_text):
        """Updates the generated narrative text."""
        if name in self.rpts_dict:
            self.rpts_dict[name].secti = final_text

    def edit_report_narrative_inputs(self, name, billet, accomplishments, user_context, s_prompt, u_prompt):
        """Updates the input data (billet/bullets/context) used for generation."""
        if name in self.rpts_dict:
            self.rpts_dict[name].billet = billet
            self.rpts_dict[name].accomplishments = accomplishments
            self.rpts_dict[name].context = user_context
            self.rpts_dict[name].prompt["system"] = s_prompt
            self.rpts_dict[name].prompt["user"] = u_prompt

    def get_report_by_name(self, name):
        return self.rpts_dict[name]

    def get_num_reports(self):
        return len(self.name_list)

    def is_name_in_db(self, name):
        return name in self.name_list

    def increment_report_gen_counter(self, name):
        if name in self.rpts_dict:
            self.rpts_dict[name].secti_gens += 1

    def __repr__(self):
        res_str = ""
        for name in self.name_list:
            res_str += f"{self.rpts_dict[name]}\n\n"
        return res_str

####################################################################################
########################  Config/Example Data class ################################
####################################################################################
class ExampleData:
    """
    A data class that loads data from config .yaml files and stores them use in the app.
    """
    def __init__(self):
        """
        Loads all YAML data into memory upon instantiation.
        """
        self.base_dir = Path(__file__).resolve().parent / "examples"
        self.examples = self._load_examples()
        self.recs = self._load_recs()

    def _load_examples(self):
        """Loads example narratives into a tiered dictionary."""
        data = {}
        mapping = {
            'bottom_third.yaml': 'bottom_third',
            'middle_third.yaml': 'middle_third',
            'top_third.yaml': 'top_third',
            'water_walkers.yaml': 'water_walkers'
        }

        for fname, key in mapping.items():
            path = self.base_dir / fname
            if path.exists():
                with open(path, "r", encoding="utf8") as f:
                    data[key] = yaml.safe_load(f)
            else:
                data[key] = []
        return data

    def _load_recs(self):
        """Loads the recommendations database."""
        path = self.base_dir / "recommendations.yaml"
        if path.exists():
            with open(path, "r", encoding="utf8") as f:
                return yaml.safe_load(f)
        return {}
