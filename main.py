import time
import json
import math
from pathlib import Path

EPSILON = 1e-9
BENCHMARK_REPEAT = 100
MAX_GENERATED_SIZE = 1000

# 정해진 크기의 숫자 배열을 입력받는 함수
def read_matrix(name, size):
    matrix = []

    print(f"\n{name}: 각 줄에 숫자 {size}개를 입력하세요.")
    print("첫 번째 줄에 cross 또는 x를 입력하면 자동 생성합니다.")

    for row in range(size):
        while True:
            line = input(f"{row + 1}번째 줄: ")

            if row == 0 and line.strip().lower() in ("cross", "x"):
                matrix = (
                    make_cross(size) if line.strip().lower() == "cross"
                    else make_x(size)
                )
                print_matrix(matrix)
                return matrix

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
    # 입력과 필터의 같은 위치를 곱하고, 곱한 값을 누적해 점수로 반환한다.
    score = 0.0
    size = len(pattern)

    for row in range(size):
        for col in range(size):
            score += pattern[row][col] * filter_data[row][col]

    return score


def flatten_matrix(matrix):
    """행 순서를 유지해 N×N 배열을 길이 N²의 리스트로 바꾼다."""
    flat = []
    for row in matrix:
        for value in row:
            flat.append(value)
    return flat


def mac_flat(pattern, filter_data):
    """1차원 배열을 같은 순서로 곱하고 누적한다."""
    if len(pattern) != len(filter_data):
        raise ValueError("1차원 패턴과 필터 길이가 다릅니다.")
    score = 0.0
    for index in range(len(pattern)):
        score += pattern[index] * filter_data[index]
    return score


def compare_mac(pattern, filter_data, repeat=BENCHMARK_REPEAT):
    """같은 값과 같은 반복 횟수로 2차원·1차원 MAC을 비교한다."""
    if isinstance(repeat, bool) or not isinstance(repeat, int) or repeat < 1:
        raise ValueError("반복 횟수는 1 이상의 정수여야 합니다.")
    size = len(pattern)
    validate_size(size)
    validate_matrix(pattern, size, "입력 패턴")
    validate_matrix(filter_data, size, "필터")

    conversion_start = time.perf_counter()
    flat_pattern = flatten_matrix(pattern)
    flat_filter = flatten_matrix(filter_data)
    conversion_ms = (time.perf_counter() - conversion_start) * 1000

    # 정확성을 먼저 확인하고, 첫 호출의 영향을 줄인 뒤 시간을 측정한다.
    score_2d = mac(pattern, filter_data)
    score_1d = mac_flat(flat_pattern, flat_filter)
    if score_2d != score_1d:
        raise ValueError("2차원과 1차원 MAC 점수가 다릅니다.")

    total = {"2D": 0.0, "1D": 0.0}
    operations = (
        ("2D", mac, pattern, filter_data),
        ("1D", mac_flat, flat_pattern, flat_filter),
    )
    for index in range(repeat):
        # 순서를 번갈아 실행해 한쪽이 항상 먼저 실행되는 영향을 줄인다.
        order = operations if index % 2 == 0 else operations[::-1]
        for name, operation, values, weights in order:
            start = time.perf_counter()
            operation(values, weights)
            end = time.perf_counter()
            total[name] += end - start

    average_2d = total["2D"] / repeat * 1000
    average_1d = total["1D"] / repeat * 1000
    return {
        "size": size,
        "repeat": repeat,
        "score_2d": score_2d,
        "score_1d": score_1d,
        "time_2d_ms": average_2d,
        "time_1d_ms": average_1d,
        "conversion_ms": conversion_ms,
        "speedup": average_2d / average_1d if average_1d > 0 else None,
    }


def print_comparison(results):
    print("\n[1차원 배열 최적화 비교]")
    print(f"동일 입력, 각 방식 {results[0]['repeat']}회 평균 / 시간 단위: ms")
    print("변환은 패턴·필터 두 배열을 1회 변환한 시간이며 MAC 평균에서 제외")
    print("크기 / 2D 평균 / 1D 평균 / 2D÷1D / 변환 시간 / 점수 일치")
    for result in results:
        ratio = (
            f"{result['speedup']:.2f}배" if result["speedup"] is not None
            else "측정 불가"
        )
        size = result["size"]
        print(
            f"{size}×{size} / {result['time_2d_ms']:.6f} / "
            f"{result['time_1d_ms']:.6f} / {ratio} / "
            f"{result['conversion_ms']:.6f} / PASS"
        )
    print("2D÷1D가 1보다 크면 해당 실행에서는 1D 계산이 더 빠릅니다.")

# MAC 함수 한 번의 실행 시간을 반복 측정해 평균 내기
def measure_mac(pattern, filter_data, repeat=10):
    total_seconds = 0.0

    for _ in range(repeat):
        # 측정 시작: 배열 생성과 입출력은 포함하지 않는다.
        start = time.perf_counter()
        mac(pattern, filter_data)
        end = time.perf_counter()
        # 측정 종료: MAC 함수 호출 구간만 초 단위로 기록한다.

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

    if abs(score_a - score_b) < EPSILON:
        result = "판정 불가"
    elif score_a > score_b:
        result = "A"
    else:
        result = "B"

    print("\nA 점수:", score_a)
    print("B 점수:", score_b)
    print("판정:", result)

    print("\n성능 분석: MAC 함수 1회 기준, 10회 평균")
    print("필터 / 크기 / 평균 시간(ms) / MAC 횟수(N²)")
    # 필터 A와 B를 각각 측정하며 출력 시간은 측정에 포함하지 않는다.
    for name, filter_data in (("A", filter_a), ("B", filter_b)):
        average_ms = measure_mac(pattern, filter_data)
        print(f"{name} / 3×3 / {average_ms:.6f} / {len(pattern) ** 2}")

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
        raise ValueError(
            f"알 수 없는 라벨: {label!r}. 허용 예: +, cross, Cross, x, X"
        )

def validate_size(size):
    if isinstance(size, bool) or not isinstance(size, int) or size < 1:
        raise ValueError("크기는 1 이상의 정수여야 합니다.")


# 지정한 크기의 십자가 배열 생성
def make_cross(size):
    validate_size(size)
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


def make_x(size):
    validate_size(size)
    matrix = []
    for row in range(size):
        line = []
        for col in range(size):
            line.append(1.0 if row == col or row + col == size - 1 else 0.0)
        matrix.append(line)
    return matrix


def print_matrix(matrix):
    # 큰 배열도 생성·계산하되, 콘솔에 수백만 칸을 출력하지 않는다.
    if len(matrix) > 25:
        print(f"{len(matrix)}×{len(matrix)} 배열 생성 완료 (25 초과는 화면 출력 생략)")
        return
    for row in matrix:
        print(" ".join(f"{value:g}" for value in row))


def run_generator():
    while True:
        try:
            size = int(input(f"패턴 크기 N (1~{MAX_GENERATED_SIZE}): "))
            if not 1 <= size <= MAX_GENERATED_SIZE:
                raise ValueError
            break
        except ValueError:
            print(f"1~{MAX_GENERATED_SIZE} 사이의 정수를 입력하세요.")

    cross = make_cross(size)
    x = make_x(size)
    print("\n[생성한 Cross]")
    print_matrix(cross)
    print("\n[생성한 X]")
    print_matrix(x)

    print("\n[생성 패턴 판정]")
    for name, pattern in (("Cross", cross), ("X", x)):
        cross_score = mac(pattern, cross)
        x_score = mac(pattern, x)
        if abs(cross_score - x_score) < EPSILON:
            result = "UNDECIDED"
        else:
            result = "Cross" if cross_score > x_score else "X"
        print(f"{name} 입력: Cross={cross_score:g}, X={x_score:g}, 판정={result}")
    print("크기가 작아 두 모양이 같으면 UNDECIDED가 나올 수 있습니다.")
    print_comparison([compare_mac(cross, cross)])


def run_optimization():
    results = []
    for size in (3, 5, 13, 25):
        pattern = make_cross(size)
        filter_data = make_cross(size)
        results.append(compare_mac(pattern, filter_data))
    print_comparison(results)

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
                raise ValueError(
                    "패턴 이름은 size_N_번호 형식이어야 합니다. 예: size_5_1"
                )

            size = int(parts[1])

            if size < 1:
                raise ValueError("패턴 크기는 1 이상이어야 합니다.")

            # 해당 크기의 필터 가져오기
            filter_key = f"size_{size}"
            if filter_key not in data["filters"]:
                available = ", ".join(data["filters"]) or "없음"
                raise ValueError(
                    f"필터 {filter_key}가 없습니다. 사용 가능한 키: {available}. "
                    "패턴 이름의 N과 필터 키의 크기를 확인하세요."
                )
            raw_filters = data["filters"][filter_key]

            if not isinstance(raw_filters, dict):
                raise ValueError(
                    f"{filter_key}: 필터 묶음은 객체여야 합니다."
                )

            # 필터 이름도 Cross와 X로 정규화
            filters = {}

            for label, matrix in raw_filters.items():
                standard_label = normalize_label(label)
                if standard_label in filters:
                    raise ValueError(f"{standard_label} 필터 라벨이 중복되었습니다.")
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
            if abs(score_cross - score_x) < EPSILON:
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
                        "[TIE] 두 점수 차이가 1e-9 미만이므로 동점 처리"
                        f" (expected: {expected})"
                    )
                else:
                    reason = (
                        f"[MISMATCH] 판정 {result}와 기대 정답 {expected}가 다름"
                    )

                failures.append((pattern_key, reason))

            print(f"Cross 점수: {score_cross:.10f}")
            print(f"X 점수: {score_x:.10f}")
            print(f"판정: {result} | expected: {expected} | {status}")

        except (KeyError, ValueError) as error:
            reason = f"[DATA] 데이터 키 또는 값 오류: {error}"
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
    print("3. Cross/X 패턴 생성 및 성능 비교")
    print("4. 크기별 2D/1D 최적화 비교")

    while True:
        choice = input("선택: ").strip()

        if choice == "1":
            run_manual()
            break
        elif choice == "2":
            run_json()
            break
        elif choice == "3":
            run_generator()
            break
        elif choice == "4":
            run_optimization()
            break
        else:
            print("1, 2, 3, 4 중 하나를 입력하세요.")


if __name__ == "__main__":
    main()
