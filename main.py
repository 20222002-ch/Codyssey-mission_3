import time
import json
import math
from pathlib import Path

# 정해진 크기의 숫자 배열을 입력받는 함수
def read_matrix(name, size):
    matrix = []

    print(f"\n{name}: 각 줄에 숫자 {size}개를 입력하세요.")

    for row in range(size):
        while True:
            line = input(f"{row + 1}번째 줄: ")

            try:
                numbers = [float(value) for value in line.split()]

                if len(numbers) != size:
                    print(f"입력 형식 오류: 숫자를 {size}개 입력하세요.")
                    continue

                if not all(math.isfinite(value) for value in numbers):
                    print("입력 형식 오류: nan과 inf는 사용할 수 없습니다.")
                    continue

                matrix.append(numbers)
                break

            except ValueError:
                print("입력 형식 오류: 숫자만 입력하세요.")

    return matrix

# 배열의 행 수, 열 수, 숫자 여부 검사
def validate_matrix(matrix, size, name):
    if not isinstance(matrix, list):
        raise ValueError(f"{name}: 배열이어야 합니다.")

    if len(matrix) != size:
        raise ValueError(f"{name}: 행 수가 {size}개여야 합니다.")

    for row_index, row in enumerate(matrix):
        if not isinstance(row, list):
            raise ValueError(
                f"{name}: {row_index + 1}번째 행이 배열이 아닙니다."
            )

        if len(row) != size:
            raise ValueError(
                f"{name}: {row_index + 1}번째 행의 숫자가 "
                f"{size}개여야 합니다."
            )

        for value in row:
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(
                    f"{name}: {row_index + 1}번째 행에 "
                    "숫자가 아닌 값이 있습니다."
                )

            if isinstance(value, float) and not math.isfinite(value):
                raise ValueError(
                    f"{name}: {row_index + 1}번째 행에 "
                    "nan 또는 inf가 있습니다."
                )

# 패턴과 필터의 MAC 점수를 계산하는 함수
def mac(pattern, filter_data):
    score = 0.0
    size = len(pattern)

    for row in range(size):
        for col in range(size):
            score += pattern[row][col] * filter_data[row][col]

    return score

# MAC 함수 한 번의 실행 시간을 반복 측정해 평균 내기
def measure_mac(pattern, filter_data, repeat=10):
    total_seconds = 0.0

    for _ in range(repeat):
        start = time.perf_counter()
        mac(pattern, filter_data)
        end = time.perf_counter()

        total_seconds += end - start

    average_ms = (total_seconds / repeat) * 1000
    return average_ms

# 모드 1: 사용자 입력
def run_manual():
    filter_a = read_matrix("필터 A", 3)
    filter_b = read_matrix("필터 B", 3)

    print("\n필터 A 저장 완료:", filter_a)
    print("필터 B 저장 완료:", filter_b)

    pattern = read_matrix("입력 패턴", 3)

    score_a = mac(pattern, filter_a)
    score_b = mac(pattern, filter_b)

    epsilon = 1e-9

    if abs(score_a - score_b) < epsilon:
        result = "판정 불가"
    elif score_a > score_b:
        result = "A"
    else:
        result = "B"

    print("\nA 점수:", score_a)
    print("B 점수:", score_b)
    print("판정:", result)

    average_ms = measure_mac(pattern, filter_a)

    print("\n성능 분석: MAC 함수 1회 기준, 10회 평균")
    print("크기 / 평균 시간(ms) / MAC 횟수(N²)")
    print(f"3×3 / {average_ms:.6f} / {len(pattern) ** 2}")

# 라벨을 Cross 또는 X로 통일
def normalize_label(label):
    if not isinstance(label, str):
        raise ValueError("라벨은 문자열이어야 합니다.")

    label = label.strip().lower()

    if label in ("+", "cross"):
        return "Cross"
    elif label == "x":
        return "X"
    else:
        raise ValueError(f"알 수 없는 라벨: {label}")

# 지정한 크기의 십자가 배열 생성
def make_cross(size):
    matrix = []
    center = size // 2

    for row in range(size):
        line = []

        for col in range(size):
            if row == center or col == center:
                line.append(1.0)
            else:
                line.append(0.0)

        matrix.append(line)

    return matrix

# 크기별 MAC 성능 측정
def print_json_performance():
    print("\n[성능 분석]")
    print("생성한 십자가 패턴과 필터 사용")
    print("MAC 함수 1회 기준, 10회 평균")
    print("크기 / 평균 시간(ms) / MAC 횟수(N²)")

    for size in (3, 5, 13, 25):
        pattern = make_cross(size)
        filter_data = make_cross(size)

        average_ms = measure_mac(pattern, filter_data)

        print(
            f"{size}×{size} / "
            f"{average_ms:.6f} / "
            f"{size ** 2}"
        )

# 모드 2: JSON 파일 읽기
def run_json():
    # main.py가 있는 폴더에서 data.json 찾기
    data_path = Path(__file__).resolve().parent / "data.json"

    try:
        with data_path.open(encoding="utf-8-sig") as file:
            data = json.load(file)

    except FileNotFoundError:
        print("파일을 찾을 수 없습니다:", data_path)
        print("main.py와 같은 폴더에 data.json을 넣어 주세요.")
        return

    except json.JSONDecodeError as error:
        print("JSON 파일 형식에 오류가 있습니다:", error)
        return

    except (OSError, UnicodeError) as error:
        print("파일을 읽을 수 없습니다:", error)
        return

    # JSON 전체 구조 검사
    if not isinstance(data, dict):
        print("데이터 구조 오류: 최상위 데이터는 객체여야 합니다.")
        return

    if not isinstance(data.get("filters"), dict):
        print("데이터 구조 오류: filters 객체가 필요합니다.")
        return

    if not isinstance(data.get("patterns"), dict):
        print("데이터 구조 오류: patterns 객체가 필요합니다.")
        return

    print("\ndata.json 로드 완료")
    print("\n[필터 목록]")
    for filter_key in data["filters"]:
        print("-", filter_key)

    total_count = len(data["patterns"])
    pass_count = 0
    failures = []

    for pattern_key, case in data["patterns"].items():
        print(f"\n--- {pattern_key} ---")

        try:
            # 개별 케이스 구조 검사
            if not isinstance(case, dict):
                raise ValueError("케이스는 객체여야 합니다.")
            # 패턴 이름에서 크기 추출
            parts = pattern_key.split("_")

            if (
                len(parts) != 3
                or parts[0] != "size"
                or not parts[1].isdigit()
                or not parts[2].isdigit()
            ):
                raise ValueError("패턴 이름은 size_N_번호 형식이어야 합니다.")

            size = int(parts[1])

            if size < 1:
                raise ValueError("패턴 크기는 1 이상이어야 합니다.")

            # 해당 크기의 필터 가져오기
            filter_key = f"size_{size}"
            raw_filters = data["filters"][filter_key]

            if not isinstance(raw_filters, dict):
                raise ValueError(
                    f"{filter_key}: 필터 묶음은 객체여야 합니다."
                )

            # 필터 이름도 Cross와 X로 정규화
            filters = {}

            for label, matrix in raw_filters.items():
                standard_label = normalize_label(label)
                filters[standard_label] = matrix

            # 입력 패턴과 기대 정답 가져오기
            pattern = case["input"]
            expected = normalize_label(case["expected"])

            # 계산 전에 패턴과 두 필터의 크기 및 숫자 검사
            validate_matrix(pattern, size, "입력 패턴")
            validate_matrix(filters["Cross"], size, "Cross 필터")
            validate_matrix(filters["X"], size, "X 필터")

            # MAC 점수 계산
            score_cross = mac(pattern, filters["Cross"])
            score_x = mac(pattern, filters["X"])

            # 허용오차를 적용해서 판정
            if abs(score_cross - score_x) < 1e-9:
                result = "UNDECIDED"
            elif score_cross > score_x:
                result = "Cross"
            else:
                result = "X"

            if result == expected:
                status = "PASS"
                pass_count += 1

            else:
                status = "FAIL"

                if result == "UNDECIDED":
                    reason = (
                        "두 점수 차이가 1e-9 미만이므로 동점 처리"
                        f" (expected: {expected})"
                    )
                else:
                    reason = (
                        f"판정 {result}와 기대 정답 {expected}가 다름"
                    )

                failures.append((pattern_key, reason))

            print(f"Cross 점수: {score_cross:.10f}")
            print(f"X 점수: {score_x:.10f}")
            print(f"판정: {result} | expected: {expected} | {status}")

        except (KeyError, ValueError) as error:
            reason = f"데이터 키 또는 값 오류: {error}"
            failures.append((pattern_key, reason))
            print(f"FAIL: {reason}")

    print_json_performance()

    print("\n[결과 요약]")
    print(f"총 테스트: {total_count}개")
    print(f"통과: {pass_count}개")
    print(f"실패: {len(failures)}개")

    if failures:
        print("\n실패 케이스:")

        for case_name, reason in failures:
            print(f"- {case_name}: {reason}")

    else:
        print("\n모든 케이스를 통과했습니다.")


# 프로그램 시작과 모드 선택
def main():
    print("=== Mini NPU Simulator ===")
    print("1. 사용자 입력 (3×3)")
    print("2. data.json 분석")

    while True:
        choice = input("선택: ").strip()

        if choice == "1":
            run_manual()
            break
        elif choice == "2":
            run_json()
            break
        else:
            print("1 또는 2를 입력하세요.")


if __name__ == "__main__":
    main()