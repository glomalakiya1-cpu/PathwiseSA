"""
Pathwise SA - South African Youth Opportunity & Matric APS Matcher
Runs directly in Pydroid 3 on Android.
"""

from dataclasses import dataclass
from typing import List, Dict

# =====================================================================
# 1. NSC Matric Scoring & APS Rules
# =====================================================================

def score_to_nsc_level(percentage: int) -> int:
    """Converts a Matric subject mark (0-100%) to NSC Level (1-7)."""
    if percentage >= 80:
        return 7
    elif percentage >= 70:
        return 6
    elif percentage >= 60:
        return 5
    elif percentage >= 50:
        return 4
    elif percentage >= 40:
        return 3
    elif percentage >= 30:
        return 2
    else:
        return 1

def get_pass_qualification(scores: List[int], total_aps: int) -> str:
    """Evaluates Bachelor's, Diploma, or Higher Certificate pass."""
    level4_count = sum(1 for s in scores if s >= 50)
    level3_count = sum(1 for s in scores if s >= 40)

    if level4_count >= 4 and total_aps >= 23:
        return "Bachelor's Degree Pass (B Deg)"
    elif level3_count >= 4 and total_aps >= 19:
        return "Diploma Pass (Dip)"
    elif total_aps >= 15:
        return "Higher Certificate Pass (HCert)"
    else:
        return "National Senior Certificate"

# =====================================================================
# 2. Data Models
# =====================================================================

@dataclass
class UserProfile:
    full_name: str = "Thabo Mokoena"
    province: str = "Gauteng"
    grade_or_status: str = "Grade 12 / Matric"
    field_of_interest: str = "Technology & IT"
    household_income_bracket: str = "Under R350,000 (NSFAS Eligible)"
    has_pure_maths: bool = True
    home_language_score: int = 74
    first_additional_language_score: int = 78
    maths_score: int = 76
    life_orientation_score: int = 82
    elective1_name: str = "Physical Sciences"
    elective1_score: int = 72
    elective2_name: str = "Information Technology"
    elective2_score: int = 84
    elective3_name: str = "Accounting"
    elective3_score: int = 68
    count_lo_in_aps: bool = False

    def get_aps(self) -> int:
        l1 = score_to_nsc_level(self.home_language_score)
        l2 = score_to_nsc_level(self.first_additional_language_score)
        l3 = score_to_nsc_level(self.maths_score)
        l4 = score_to_nsc_level(self.elective1_score)
        l5 = score_to_nsc_level(self.elective2_score)
        l6 = score_to_nsc_level(self.elective3_score)
        lo = (score_to_nsc_level(self.life_orientation_score) // 2) if self.count_lo_in_aps else 0
        return l1 + l2 + l3 + l4 + l5 + l6 + lo

    def get_pass_level(self) -> str:
        scores = [
            self.home_language_score,
            self.first_additional_language_score,
            self.maths_score,
            self.elective1_score,
            self.elective2_score,
            self.elective3_score,
        ]
        return get_pass_qualification(scores, self.get_aps())

@dataclass
class Opportunity:
    id: str
    title: str
    provider: str
    category: str
    field: str
    description: str
    min_aps: int = 0
    requires_pure_maths: bool = False
    min_maths_score: int = 0
    min_english_score: int = 50
    max_household_income: int = 0
    provinces: str = "All South Africa"
    stipend_or_funding: str = ""
    closing_date: str = ""
    official_url: str = ""

    def evaluate_match(self, user: UserProfile) -> Dict:
        score = 100
        reasons = []
        warnings = []
        user_aps = user.get_aps()

        # APS check
        if self.min_aps > 0:
            if user_aps >= self.min_aps:
                excess = user_aps - self.min_aps
                reasons.append(f"APS ({user_aps}) meets min requirement ({self.min_aps})")
            else:
                diff = self.min_aps - user_aps
                score -= min(diff * 7, 35)
                warnings.append(f"APS below minimum (You have {user_aps}, requires {self.min_aps})")
        else:
            reasons.append("No minimum APS prerequisite required")

        # Pure Maths check
        if self.requires_pure_maths:
            if not user.has_pure_maths:
                score -= 30
                warnings.append("Requires Pure Mathematics (You have Maths Literacy)")
            elif user.maths_score >= self.min_maths_score:
                reasons.append(f"Pure Maths ({user.maths_score}%) satisfies min {self.min_maths_score}%")
            else:
                score -= 20
                warnings.append(f"Pure Maths ({user.maths_score}%) is below {self.min_maths_score}%")
        elif self.min_maths_score > 0:
            if user.maths_score >= self.min_maths_score:
                reasons.append(f"Maths score ({user.maths_score}%) satisfies requirement")
            else:
                score -= 15
                warnings.append(f"Maths score ({user.maths_score}%) below {self.min_maths_score}%")

        # English check
        best_eng = max(user.home_language_score, user.first_additional_language_score)
        if best_eng >= self.min_english_score:
            reasons.append(f"English requirement satisfied ({best_eng}% >= {self.min_english_score}%)")
        else:
            score -= 15
            warnings.append(f"English score ({best_eng}%) below {self.min_english_score}%")

        # Income check
        if self.max_household_income > 0:
            is_nsfas = "Under R350,000" in user.household_income_bracket
            if self.max_household_income == 350000 and is_nsfas:
                reasons.append("Income meets threshold (Under R350k/yr)")
            elif not is_nsfas and self.max_household_income == 350000:
                score -= 30
                warnings.append("Strictly requires household income under R350,000/yr")

        final_score = max(10, min(99, score))
        is_eligible = len(warnings) == 0 or (len(warnings) == 1 and final_score >= 70)

        return {
            "percentage": final_score,
            "is_eligible": is_eligible,
            "reasons": reasons,
            "warnings": warnings,
        }

# =====================================================================
# 3. Real South African Opportunities Catalog
# =====================================================================

OPPORTUNITIES = [
    Opportunity(
        id="nsfas",
        title="NSFAS Higher Education Bursary",
        provider="DHET / South African Government",
        category="BURSARY",
        field="All Fields",
        description="Comprehensive funding for tuition, accommodation, meals, laptop & personal allowance.",
        min_aps=23,
        requires_pure_maths=False,
        min_maths_score=40,
        min_english_score=50,
        max_household_income=350000,
        provinces="All South Africa",
        stipend_or_funding="100% Tuition + R16,500/yr living allowance + R5,460 books + Housing",
        closing_date="31 January 2027",
        official_url="https://www.nsfas.org.za"
    ),
    Opportunity(
        id="wethinkcode",
        title="Tuition-Free Software Engineering Learnership",
        provider="WeThinkCode_",
        category="LEARNERSHIP",
        field="Technology & IT",
        description="2-year coding academy in Johannesburg, Cape Town, and Durban.",
        min_aps=0,
        requires_pure_maths=False,
        min_maths_score=0,
        min_english_score=40,
        max_household_income=0,
        provinces="Gauteng, Western Cape, KwaZulu-Natal",
        stipend_or_funding="Full tuition waiver (R120k value) + monthly transport stipend + guaranteed internship",
        closing_date="Open Year-Round",
        official_url="https://www.wethinkcode.co.za"
    ),
    Opportunity(
        id="sasol",
        title="Sasol STEM & Engineering Bursary",
        provider="Sasol Foundation",
        category="BURSARY",
        field="Engineering & Built Env.",
        description="Undergraduate studies in Chemical, Mechanical, Electrical, Mining Engineering and Data Science.",
        min_aps=32,
        requires_pure_maths=True,
        min_maths_score=70,
        min_english_score=60,
        max_household_income=0,
        provinces="All South Africa",
        stipend_or_funding="Full tuition, residence, meals, R12k laptop allowance & vacation work pay",
        closing_date="30 November 2026",
        official_url="https://www.sasolbursaries.com"
    ),
    Opportunity(
        id="allan_gray",
        title="Allan Gray Orbis Fellowship",
        provider="Allan Gray Orbis Foundation",
        category="SCHOLARSHIP",
        field="Business, Commerce & Accounting",
        description="Full university funding with leadership and entrepreneurial mindset coaching.",
        min_aps=35,
        requires_pure_maths=True,
        min_maths_score=70,
        min_english_score=65,
        max_household_income=0,
        provinces="All South Africa",
        stipend_or_funding="Tuition, residence, personal stipend & startup incubation grants",
        closing_date="30 April 2027",
        official_url="https://www.allangrayorbis.org"
    ),
    Opportunity(
        id="standard_bank",
        title="Standard Bank CSI 150 Bursary",
        provider="Standard Bank Group",
        category="BURSARY",
        field="Business, Commerce & Accounting",
        description="Bursaries in Commerce, Actuarial Science, Data Analytics, Computer Science, and Engineering.",
        min_aps=32,
        requires_pure_maths=True,
        min_maths_score=65,
        min_english_score=60,
        max_household_income=600000,
        provinces="All South Africa",
        stipend_or_funding="Full tuition, student housing, laptop & R15,000 allowance",
        closing_date="15 December 2026",
        official_url="https://www.standardbank.co.za"
    ),
    Opportunity(
        id="capitec",
        title="Capitec Data & Software Internship",
        provider="Capitec Bank",
        category="INTERNSHIP",
        field="Technology & IT",
        description="18-month paid development programme at Capitec tech hubs in Stellenbosch & JHB.",
        min_aps=28,
        requires_pure_maths=False,
        min_maths_score=60,
        min_english_score=60,
        max_household_income=0,
        provinces="Western Cape, Gauteng",
        stipend_or_funding="R18,000 - R24,000 / month salary + relocation allowance",
        closing_date="28 February 2027",
        official_url="https://www.capitecbank.co.za/careers"
    ),
    Opportunity(
        id="yes4youth",
        title="YES4Youth 12-Month Work Experience",
        provider="Youth Employment Service (YES)",
        category="LEARNERSHIP",
        field="All Fields",
        description="12-month paid work experience in blue-chip corporations across banking, retail, and tech.",
        min_aps=0,
        requires_pure_maths=False,
        min_maths_score=0,
        min_english_score=40,
        max_household_income=0,
        provinces="All South Africa",
        stipend_or_funding="R4,500 - R7,500/month stipend + verified reference certificate",
        closing_date="Open Year-Round",
        official_url="https://www.yes4youth.co.za"
    ),
    Opportunity(
        id="uct_vc",
        title="UCT Vice-Chancellor's Regional Scholarship",
        provider="University of Cape Town (UCT)",
        category="UNIVERSITY",
        field="All Fields",
        description="Merit and financial-need scholarship for top matriculants from public high schools.",
        min_aps=38,
        requires_pure_maths=False,
        min_maths_score=65,
        min_english_score=70,
        max_household_income=350000,
        provinces="All South Africa",
        stipend_or_funding="Full cost of study (tuition, Upper Campus residence, books, living allowance)",
        closing_date="31 October 2026",
        official_url="https://www.uct.ac.za"
    )
]

# =====================================================================
# 4. Interactive CLI Interface
# =====================================================================

def main():
    print("=" * 60)
    print("      PATHWISE SA - South African Youth Opportunity Matcher")
    print("=" * 60)

    user = UserProfile()

    while True:
        print("\nChoose an option:")
        print("  [1] View Current Profile & Matric APS Score")
        print("  [2] Enter Custom Matric Subject Marks (%)")
        print("  [3] Show Top Matched Opportunities")
        print("  [4] Filter Opportunities by Category")
        print("  [5] Export CV / Matric Summary")
        print("  [0] Exit")

        choice = input("\nEnter choice (0-5): ").strip()

        if choice == "0":
            print("\nSalani kahle / Goodbye!")
            break
        elif choice == "1":
            print("\n--- YOUR MATRIC PROFILE ---")
            print(f"Name:             {user.full_name}")
            print(f"Province:         {user.province}")
            print(f"Status:           {user.grade_or_status}")
            print(f"Calculated APS:   {user.get_aps()} points")
            print(f"Pass Type:        {user.get_pass_level()}")
            math_type = "Pure Maths" if user.has_pure_maths else "Maths Literacy"
            print(f"Mathematics:      {math_type} ({user.maths_score}%, Level {score_to_nsc_level(user.maths_score)})")
            print(f"Home Language:    {user.home_language_score}% (Level {score_to_nsc_level(user.home_language_score)})")
            print(f"First Add. Lang:  {user.first_additional_language_score}% (Level {score_to_nsc_level(user.first_additional_language_score)})")
            print(f"{user.elective1_name}: {user.elective1_score}% (Level {score_to_nsc_level(user.elective1_score)})")
            print(f"{user.elective2_name}: {user.elective2_score}% (Level {score_to_nsc_level(user.elective2_score)})")
            print(f"{user.elective3_name}: {user.elective3_score}% (Level {score_to_nsc_level(user.elective3_score)})")
        elif choice == "2":
            print("\n--- ENTER MARKS (0-100) ---")
            try:
                user.home_language_score = int(input("Home Language % [75]: ") or "75")
                user.first_additional_language_score = int(input("First Additional Language % [78]: ") or "78")
                m_type = input("Maths Type? (p = Pure Maths, l = Maths Lit) [p]: ").strip().lower()
                user.has_pure_maths = (m_type != "l")
                user.maths_score = int(input(f"{'Pure Maths' if user.has_pure_maths else 'Maths Lit'} % [70]: ") or "70")
                user.elective1_name = input("Elective 1 name [Physical Sciences]: ") or "Physical Sciences"
                user.elective1_score = int(input(f"{user.elective1_name} % [72]: ") or "72")
                user.elective2_name = input("Elective 2 name [Information Technology]: ") or "Information Technology"
                user.elective2_score = int(input(f"{user.elective2_name} % [75]: ") or "75")
                user.elective3_name = input("Elective 3 name [Accounting]: ") or "Accounting"
                user.elective3_score = int(input(f"{user.elective3_name} % [68]: ") or "68")

                print(f"\n>> UPDATED APS: {user.get_aps()} points")
                print(f">> Qualification: {user.get_pass_level()}")
            except ValueError:
                print("Error: Please enter integer percentage numbers.")
        elif choice == "3":
            print(f"\n--- MATCHED OPPORTUNITIES (Your APS: {user.get_aps()}) ---")
            matches = [(opp, opp.evaluate_match(user)) for opp in OPPORTUNITIES]
            matches.sort(key=lambda x: x[1]["percentage"], reverse=True)

            for i, (opp, res) in enumerate(matches, 1):
                badge = "[ELIGIBLE]" if res["is_eligible"] else "[PARTIAL]"
                print(f"\n{i}. {opp.title} ({opp.provider})")
                print(f"   Match:   {res['percentage']}% {badge} | Category: {opp.category}")
                print(f"   Funding: {opp.stipend_or_funding}")
                print(f"   Min APS: {opp.min_aps} | Portal: {opp.official_url}")
                if res["reasons"]:
                    print(f"   ✓ {res['reasons'][0]}")
                if res["warnings"]:
                    print(f"   ⚠ {res['warnings'][0]}")
        elif choice == "4":
            cat = input("\nEnter category (BURSARY, LEARNERSHIP, INTERNSHIP, UNIVERSITY): ").strip().upper()
            found = [o for o in OPPORTUNITIES if not cat or o.category == cat]
            print(f"\nFound {len(found)} opportunities:")
            for o in found:
                m = o.evaluate_match(user)
                print(f"• [{o.category}] {o.title} - {o.provider} ({m['percentage']}% Match)")
                print(f"  Funding: {o.stipend_or_funding}")
        elif choice == "5":
            print("\n" + "=" * 50)
            print("PATHWISE SA - APPLICANT CV / ACADEMIC SUMMARY")
            print("=" * 50)
            print(f"Name:             {user.full_name}")
            print(f"Province:         {user.province}")
            print(f"Household Income: {user.household_income_bracket}")
            print(f"Calculated APS:   {user.get_aps()} points ({user.get_pass_level()})")
            print(f"Mathematics:      {'Pure Maths' if user.has_pure_maths else 'Maths Lit'} ({user.maths_score}%)")
            print(f"Home Language:    {user.home_language_score}%")
            print(f"First Add. Lang:  {user.first_additional_language_score}%")
            print(f"{user.elective1_name}: {user.elective1_score}%")
            print(f"{user.elective2_name}: {user.elective2_score}%")
            print(f"{user.elective3_name}: {user.elective3_score}%")
            print("=" * 50)

if __name__ == "__main__":
    main()
