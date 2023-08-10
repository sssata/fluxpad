#pragma once

#include <cmath>
#include <iostream>

class WelfordAlgorithm {
  public:
    WelfordAlgorithm() : count(0), mean(0.0), M2(0.0) {}

    void update(float new_value) {
        count++;
        float delta = new_value - mean;
        mean += delta / count;
        float delta2 = new_value - mean;
        M2 += delta * delta2;
    }

    float get_mean() const { return count > 0 ? mean : NAN; }

    float get_variance() const { return count > 1 ? M2 / (count - 1) : NAN; }

    float get_standard_deviation() const {
        float variance = get_variance();
        return !std::isnan(variance) ? std::sqrt(variance) : NAN;
    }

    int get_count() const { return count; }

  private:
    int count;
    float mean;
    float M2;
};

// int main() {
//     WelfordAlgorithm welford;
//     double data[] = {2, 4, 4, 4, 5, 5, 7, 9};
//     int dataSize = sizeof(data) / sizeof(data[0]);

//     for (int i = 0; i < dataSize; i++) {
//         welford.update(data[i]);
//     }

//     std::cout << "Count: " << welford.get_count() << std::endl;
//     std::cout << "Mean: " << welford.get_mean() << std::endl;
//     std::cout << "Variance: " << welford.get_variance() << std::endl;
//     std::cout << "Standard Deviation: " << welford.get_standard_deviation() << std::endl;

//     return 0;
// }
