from django.core.management.base import BaseCommand
from apps.compiler.models import CodingProblem
from apps.courses.models import Course


class Command(BaseCommand):
    help = "Seed initial coding problems with public/hidden test cases and multi-language boilerplates."

    def handle(self, *args, **options):
        course = Course.objects.first()

        problems_data = [
            {
                "title": "Two Sum",
                "slug": "two-sum",
                "difficulty": CodingProblem.Difficulty.EASY,
                "topic_name": "Arrays & Hash Maps",
                "description": (
                    "Given an array of integers `nums` and an integer `target`, return the indices of the "
                    "two numbers such that they add up to `target`.\n\n"
                    "You may assume that each input would have exactly one solution, and you may not use the "
                    "same element twice. Return the indices separated by a space (0-indexed)."
                ),
                "constraints": (
                    "- 2 <= nums.length <= 10^4\n"
                    "- -10^9 <= nums[i] <= 10^9\n"
                    "- -10^9 <= target <= 10^9\n"
                    "- Only one valid answer exists."
                ),
                "starter_codes": {
                    "python": (
                        "# Read input from standard input\n"
                        "import sys\n\n"
                        "def solve():\n"
                        "    input_data = sys.stdin.read().split()\n"
                        "    if not input_data: return\n"
                        "    target = int(input_data[0])\n"
                        "    nums = [int(x) for x in input_data[1:]]\n"
                        "    \n"
                        "    seen = {}\n"
                        "    for i, num in enumerate(nums):\n"
                        "        comp = target - num\n"
                        "        if comp in seen:\n"
                        "            print(f\"{seen[comp]} {i}\")\n"
                        "            return\n"
                        "        seen[num] = i\n\n"
                        "if __name__ == '__main__':\n"
                        "    solve()\n"
                    ),
                    "javascript": (
                        "const fs = require('fs');\n\n"
                        "function solve() {\n"
                        "    const input = fs.readFileSync(0, 'utf-8').trim().split(/\\s+/);\n"
                        "    if (!input || input.length < 2) return;\n"
                        "    const target = parseInt(input[0], 10);\n"
                        "    const nums = input.slice(1).map(Number);\n"
                        "    \n"
                        "    const map = new Map();\n"
                        "    for (let i = 0; i < nums.length; i++) {\n"
                        "        const comp = target - nums[i];\n"
                        "        if (map.has(comp)) {\n"
                        "            console.log(`${map.get(comp)} ${i}`);\n"
                        "            return;\n"
                        "        }\n"
                        "        map.set(nums[i], i);\n"
                        "    }\n"
                        "}\n"
                        "solve();\n"
                    ),
                    "cpp": (
                        "#include <iostream>\n"
                        "#include <vector>\n"
                        "#include <unordered_map>\n"
                        "using namespace std;\n\n"
                        "int main() {\n"
                        "    int target, n;\n"
                        "    if (!(cin >> target)) return 0;\n"
                        "    vector<int> nums;\n"
                        "    int val;\n"
                        "    while (cin >> val) nums.push_back(val);\n"
                        "    \n"
                        "    unordered_map<int, int> seen;\n"
                        "    for (int i = 0; i < (int)nums.size(); i++) {\n"
                        "        int comp = target - nums[i];\n"
                        "        if (seen.find(comp) != seen.end()) {\n"
                        "            cout << seen[comp] << \" \" << i << endl;\n"
                        "            return 0;\n"
                        "        }\n"
                        "        seen[nums[i]] = i;\n"
                        "    }\n"
                        "    return 0;\n"
                        "}\n"
                    )
                },
                "public_test_cases": [
                    {
                        "input": "9 2 7 11 15",
                        "expected_output": "0 1",
                        "explanation": "target is 9. nums[0] + nums[1] = 2 + 7 = 9. Output indices: 0 1."
                    },
                    {
                        "input": "6 3 2 4",
                        "expected_output": "1 2",
                        "explanation": "target is 6. nums[1] + nums[2] = 2 + 4 = 6. Output indices: 1 2."
                    }
                ],
                "hidden_test_cases": [
                    {
                        "input": "6 3 3",
                        "expected_output": "0 1"
                    },
                    {
                        "input": "-8 -3 -5 2 4",
                        "expected_output": "0 1"
                    },
                    {
                        "input": "100 10 20 30 40 50 60",
                        "expected_output": "3 5"
                    }
                ],
                "hints": [
                    "Can you solve it in O(n) time instead of the brute-force O(n^2)?",
                    "Try using a hash map / dictionary to remember the index of elements you have already seen.",
                    "For each element x, check if (target - x) is already present in your map."
                ]
            },
            {
                "title": "Palindrome String Verification",
                "slug": "palindrome-verification",
                "difficulty": CodingProblem.Difficulty.EASY,
                "topic_name": "Strings & Pointers",
                "description": (
                    "A phrase is a palindrome if, after converting all uppercase letters into lowercase letters "
                    "and removing all non-alphanumeric characters, it reads the same forward and backward.\n\n"
                    "Given a string, print `true` if it is a palindrome, or `false` otherwise."
                ),
                "constraints": (
                    "- 1 <= s.length <= 2 * 10^5\n"
                    "- s consists only of printable ASCII characters."
                ),
                "starter_codes": {
                    "python": (
                        "import sys\n\n"
                        "def is_palindrome():\n"
                        "    line = sys.stdin.read().strip()\n"
                        "    cleaned = [c.lower() for c in line if c.isalnum()]\n"
                        "    if cleaned == cleaned[::-1]:\n"
                        "        print(\"true\")\n"
                        "    else:\n"
                        "        print(\"false\")\n\n"
                        "if __name__ == '__main__':\n"
                        "    is_palindrome()\n"
                    ),
                    "javascript": (
                        "const fs = require('fs');\n"
                        "const input = fs.readFileSync(0, 'utf-8').trim();\n"
                        "const clean = input.toLowerCase().replace(/[^a-z0-9]/g, '');\n"
                        "const reversed = clean.split('').reverse().join('');\n"
                        "console.log(clean === reversed ? 'true' : 'false');\n"
                    )
                },
                "public_test_cases": [
                    {
                        "input": "A man, a plan, a canal: Panama",
                        "expected_output": "true",
                        "explanation": "\"amanaplanacanalpanama\" is a palindrome."
                    },
                    {
                        "input": "race a car",
                        "expected_output": "false",
                        "explanation": "\"raceacar\" is not a palindrome."
                    }
                ],
                "hidden_test_cases": [
                    {
                        "input": " ",
                        "expected_output": "true"
                    },
                    {
                        "input": "0P",
                        "expected_output": "false"
                    },
                    {
                        "input": "ab_a",
                        "expected_output": "true"
                    }
                ],
                "hints": [
                    "Filter out punctuation and spaces first, and convert characters to lowercase.",
                    "Use two pointers: one at the start and one at the end, moving towards the center."
                ]
            },
            {
                "title": "Valid Parentheses",
                "slug": "valid-parentheses",
                "difficulty": CodingProblem.Difficulty.MEDIUM,
                "topic_name": "Stacks",
                "description": (
                    "Given a string `s` containing just the characters '(', ')', '{', '}', '[' and ']', "
                    "determine if the input string is valid.\n\n"
                    "An input string is valid if:\n"
                    "1. Open brackets must be closed by the same type of brackets.\n"
                    "2. Open brackets must be closed in the correct order.\n"
                    "3. Every close bracket has a corresponding open bracket of the same type.\n\n"
                    "Print `true` if valid, otherwise `false`."
                ),
                "constraints": (
                    "- 1 <= s.length <= 10^4\n"
                    "- s consists of parentheses only '()[]{}'."
                ),
                "starter_codes": {
                    "python": (
                        "import sys\n\n"
                        "def is_valid():\n"
                        "    s = sys.stdin.read().strip()\n"
                        "    stack = []\n"
                        "    matching = {')': '(', '}': '{', ']': '['}\n"
                        "    for char in s:\n"
                        "        if char in matching.values():\n"
                        "            stack.append(char)\n"
                        "        elif char in matching:\n"
                        "            if not stack or stack.pop() != matching[char]:\n"
                        "                print(\"false\")\n"
                        "                return\n"
                        "    print(\"true\" if len(stack) == 0 else \"false\")\n\n"
                        "if __name__ == '__main__':\n"
                        "    is_valid()\n"
                    )
                },
                "public_test_cases": [
                    {
                        "input": "()[]{}",
                        "expected_output": "true",
                        "explanation": "All brackets closed in correct order."
                    },
                    {
                        "input": "(]",
                        "expected_output": "false",
                        "explanation": "Mismatched bracket types."
                    }
                ],
                "hidden_test_cases": [
                    {
                        "input": "([)]",
                        "expected_output": "false"
                    },
                    {
                        "input": "{[]}",
                        "expected_output": "true"
                    },
                    {
                        "input": "[",
                        "expected_output": "false"
                    }
                ],
                "hints": [
                    "A stack is the ideal data structure because the last opened bracket must be the first one closed (LIFO).",
                    "When encountering a closing bracket, check if the top of the stack matches its opening pair."
                ]
            },
            {
                "title": "Binary Search",
                "slug": "binary-search",
                "difficulty": CodingProblem.Difficulty.EASY,
                "topic_name": "Divide and Conquer",
                "description": (
                    "Given an array of integers `nums` sorted in ascending order, and an integer `target`, "
                    "write a function to search `target` in `nums`.\n\n"
                    "If `target` exists, then return its index (0-based). Otherwise, return -1.\n"
                    "You must write an algorithm with O(log n) runtime complexity."
                ),
                "constraints": (
                    "- 1 <= nums.length <= 10^4\n"
                    "- -10^4 < nums[i], target < 10^4\n"
                    "- All integers in nums are unique and sorted in ascending order."
                ),
                "starter_codes": {
                    "python": (
                        "import sys\n\n"
                        "def binary_search():\n"
                        "    data = sys.stdin.read().split()\n"
                        "    if not data: return\n"
                        "    target = int(data[0])\n"
                        "    nums = [int(x) for x in data[1:]]\n"
                        "    \n"
                        "    left, right = 0, len(nums) - 1\n"
                        "    while left <= right:\n"
                        "        mid = (left + right) // 2\n"
                        "        if nums[mid] == target:\n"
                        "            print(mid)\n"
                        "            return\n"
                        "        elif nums[mid] < target:\n"
                        "            left = mid + 1\n"
                        "        else:\n"
                        "            right = mid - 1\n"
                        "    print(-1)\n\n"
                        "if __name__ == '__main__':\n"
                        "    binary_search()\n"
                    )
                },
                "public_test_cases": [
                    {
                        "input": "9 -1 0 3 5 9 12",
                        "expected_output": "4",
                        "explanation": "Target 9 exists in nums at index 4."
                    },
                    {
                        "input": "2 -1 0 3 5 9 12",
                        "expected_output": "-1",
                        "explanation": "Target 2 does not exist in nums so return -1."
                    }
                ],
                "hidden_test_cases": [
                    {
                        "input": "5 5",
                        "expected_output": "0"
                    },
                    {
                        "input": "10 1 2 3 4 5 6 7 8 9 10",
                        "expected_output": "9"
                    }
                ],
                "hints": [
                    "Maintain left and right boundaries and inspect the midpoint in each iteration.",
                    "If target is greater than nums[mid], discard the left half by setting left = mid + 1."
                ]
            }
        ]

        count = 0
        for pdata in problems_data:
            slug = pdata.pop("slug")
            prob, created = CodingProblem.objects.update_or_create(
                slug=slug,
                defaults={
                    **pdata,
                    "course": course
                }
            )
            count += 1
            action = "Created" if created else "Updated"
            self.stdout.write(self.style.SUCCESS(f"{action} coding problem: {prob.title}"))

        self.stdout.write(self.style.SUCCESS(f"Successfully processed {count} coding problems."))
