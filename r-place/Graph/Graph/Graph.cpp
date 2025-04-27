// Graph.cpp : This file contains the 'main' function. Program execution begins and ends there.
//

#include <iostream>
#include <fstream>
#include <sstream>
#include <vector>
#include <map>
#include <ctime>
#include <filesystem>
#include <deque>
#include "Mode.h"


namespace {
    const int IMG_SIZE = 2000;
    const int MAX_COLOR = 32;
    const int HISTORY_LENGHT = 5;
    const Convolution_mode C_MODE = Plus;
    const std::string PATH = "..\\..\\";
    const Mode MODE = Convolution;
    const bool NO_WEIGHTS = false;
    const int C_FREQ = 10000000;

}

struct PixelPlacementInfo {
    int user_id_num;
    double time;
    int X, Y, color;

    PixelPlacementInfo() : user_id_num(0),time(0),X(0),Y(0),color(0) {}

    std::string toString() const {
        std::ostringstream oss;
        oss << X << " " << Y << " " << user_id_num << " " << color << " " << time;
        return oss.str();
    }
};

std::string getCurrentTime() {
    std::time_t now = std::time(0);
    struct tm timeinfo;
    char buffer[80];
    time(&now);
    localtime_s(&timeinfo, &now);
    strftime(buffer, sizeof(buffer), "%d-%m-%Y %H:%M:%S", &timeinfo);
    return std::string(buffer);
}

void readColorDistanceWeight(double color_distance_weight[][MAX_COLOR]) {
    std::ifstream file(PATH+"color_distance_weight.txt");
    for (int i = 0; i < MAX_COLOR; ++i) {
        for (int j = 0; j < MAX_COLOR; ++j) {
            file >> color_distance_weight[i][j];
        }
    }
    file.close();
}

void populatePlusShape(std::vector<std::pair<int, int>>& neighbors, int i, int j) {
    // Check left neighbor
    if (j > 0) {
        neighbors.push_back({ i, j - 1 });
    }

    // Check right neighbor
    if (j < IMG_SIZE - 1) {
        neighbors.push_back({ i, j + 1 });
    }

    // Check top neighbor
    if (i > 0) {
        neighbors.push_back({ i - 1, j });
    }

    // Check bottom neighbor
    if (i < IMG_SIZE - 1) {
        neighbors.push_back({ i + 1, j });
    }
}


std::map<std::pair<int, int>, int> readAndProcessDataConvolution(int N, double color_distance_weight[][MAX_COLOR], std::map<std::pair<int, int>, int>& graph) {

    // std::map<std::pair<int, int>, int> graph;
    std::ifstream file(PATH + "2022_place_canvas_history_timed.csv");
    std::string line;
    std::vector<std::vector<PixelPlacementInfo>> pixelArray(IMG_SIZE, std::vector<PixelPlacementInfo>(IMG_SIZE));

    std::getline(file, line);
    int c = 0;
    while (std::getline(file, line)) {

        if (c % C_FREQ == 0) {
            std::cout << c << " " << getCurrentTime() << std::endl;
        }

        //if (c == 10000000) {
        //    break;
        //}
        c++;

        std::istringstream iss(line);
        std::string token;

        // Assuming CSV structure and adjust the parsing accordingly
        PixelPlacementInfo pixelInfo;

        // Read tokens separated by commas
        std::getline(iss, token, ','); // user_id_num
        pixelInfo.user_id_num = std::stoi(token);

        std::getline(iss, token, ','); // time
        pixelInfo.time = std::stod(token);

        std::getline(iss, token, ','); // X
        pixelInfo.X = std::stoi(token);

        std::getline(iss, token, ','); // Y
        pixelInfo.Y = std::stoi(token);

        std::getline(iss, token, ','); // color
        pixelInfo.color = std::stoi(token);
       
        if (C_MODE == Square){
            for (int i = std::max(0, pixelInfo.X - 1); i <= std::min(IMG_SIZE - 1, pixelInfo.X + 1); ++i) {
                for (int j = std::max(0, pixelInfo.Y - 1); j <= std::min(IMG_SIZE - 1, pixelInfo.Y + 1); ++j) {
                    // Skip the center element, itself
                    if (not(i == pixelInfo.X && j == pixelInfo.Y)){
                        auto record = pixelArray[i][j];
                        if((record.time > 0)) {

                            auto w = color_distance_weight[pixelInfo.color][record.color];
                            int e1 = std::min(pixelInfo.user_id_num, record.user_id_num);
                            int e2 = std::max(pixelInfo.user_id_num, record.user_id_num);

                            std::pair<int, int> index = std::make_pair(e1, e2);
                            auto it = graph.find(index);


                            if (w > 0) {
                                if (it != graph.end())
                                    it->second += w;
                                else
                                    graph[index] = w;
                            }
                        }
                    }
                }
            }
        }
        else if (C_MODE == Plus) {
            std::vector<std::pair<int, int>> neighbors;
            populatePlusShape(neighbors, pixelInfo.X, pixelInfo.Y);

            for (const auto& coord : neighbors){
                int i = coord.first;
                int j = coord.second;
                auto record = pixelArray[i][j];
                if ((record.time > 0)) {

                    auto w = color_distance_weight[pixelInfo.color][record.color];
                    int e1 = std::min(pixelInfo.user_id_num, record.user_id_num);
                    int e2 = std::max(pixelInfo.user_id_num, record.user_id_num);

                    std::pair<int, int> index = std::make_pair(e1, e2);
                    auto it = graph.find(index);


                    if (w > 0) {
                        if (it != graph.end())
                            it->second += w;
                        else
                            graph[index] = w;
                    }
                }
            }
        }

        pixelArray[pixelInfo.X][pixelInfo.Y] = pixelInfo;
    }
    file.close();

    return graph;
}

std::map<std::pair<int, int>, int> readAndProcessData(int N, double color_distance_weight[][MAX_COLOR], std::map<std::pair<int, int>, int>& graph, Mode mode) {

    // std::map<std::pair<int, int>, int> graph;
    if (mode == Convolution)
    {
        return readAndProcessDataConvolution(N, color_distance_weight, graph);
    }

    std::ifstream file(PATH + "2022_place_canvas_history_grouped.csv");
    std::string line;
    std::deque<PixelPlacementInfo> recordsHistory;
    std::vector<std::vector<PixelPlacementInfo>> pixelArray;
    std::getline(file, line);
    int c = 0;
    while (std::getline(file, line)) {

        if (c % C_FREQ == 0) {
            std::cout << c << " " << getCurrentTime() << std::endl;
        }

        //if (c == 10000000) {
        //    break;
        //}
        c++;

        std::istringstream iss(line);
        std::string token;

        // Assuming CSV structure and adjust the parsing accordingly
        PixelPlacementInfo pixelInfo;

        // Read tokens separated by commas
        std::getline(iss, token, ','); // user_id_num
        pixelInfo.user_id_num = std::stoi(token);

        std::getline(iss, token, ','); // time
        pixelInfo.time = std::stod(token);

        std::getline(iss, token, ','); // X
        pixelInfo.X = std::stoi(token);

        std::getline(iss, token, ','); // Y
        pixelInfo.Y = std::stoi(token);

        std::getline(iss, token, ','); // color
        pixelInfo.color = std::stoi(token);



        // Keep only the last 5 records in the list
        if (recordsHistory.size() > HISTORY_LENGHT) {
            recordsHistory.pop_front();
        }

        while (!recordsHistory.empty() && (pixelInfo.X != recordsHistory.front().X || pixelInfo.Y != recordsHistory.front().Y)) {
            recordsHistory.pop_front();
        }

        // Print the last 5 records
        for (const auto& record : recordsHistory) {
            // std::cout << pixelInfo.toString() << " - " << record.toString() << " weight: " << color_distance_weight[pixelInfo.color][record.color] << "\n";
            auto w = color_distance_weight[pixelInfo.color][record.color];

            int e1 = std::min(pixelInfo.user_id_num, record.user_id_num);
            int e2 = std::max(pixelInfo.user_id_num, record.user_id_num);

            std::pair<int, int> index = std::make_pair(e1, e2);
            auto it = graph.find(index);

            switch (mode)
            {
            case All:
                if (it != graph.end())
                    it->second += w;
                else
                    graph[index] = w;
                break;
            case Positive:
                if (w > 0) {
                    if (it != graph.end())
                        it->second += w;
                    else
                        graph[index] = w;
                }
                break;
            case Positive_Exact:
                if (w < 0) {
                    if (it != graph.end())
                        it->second += w;
                }
                break;
            default:
                break;
            }
        }

        recordsHistory.push_back(pixelInfo);
    }
    file.close();

    return graph;
}

int main() {
    //std::filesystem::path currentPath = std::filesystem::current_path();
    //std::cout << "Current Working Directory: " << currentPath << std::endl;
    const int N = 10; // Adjust the value of N accordingly
    double color_distance_weight[MAX_COLOR][MAX_COLOR]; // Initialize this array accordingly
    readColorDistanceWeight(color_distance_weight);
    std::map<std::pair<int, int>, int> graph;
    std::string specification;
    switch (MODE)
    {
    case All:
        readAndProcessData(N, color_distance_weight, graph, All);
        specification = "" + std::to_string(HISTORY_LENGHT);
        break;
    case Positive:
        readAndProcessData(N, color_distance_weight, graph, Positive);
        specification = "positive_" + std::to_string(HISTORY_LENGHT);
        break;
    case Positive_Exact:
        readAndProcessData(N, color_distance_weight, graph, Positive);
        readAndProcessData(N, color_distance_weight, graph, Positive_Exact);
        specification = "positive_exact_" + std::to_string(HISTORY_LENGHT);
        break;
    case Convolution:
        readAndProcessData(N, color_distance_weight, graph, Convolution);
        specification = "convolution_" + std::to_string(static_cast<int>(C_MODE));
    default:
        break;
    }


    const std::string filePath = PATH + "edge_lists\\2022_graph_weighted_edges_"+ specification + ".txt";
    // Open the file for writing
    std::ofstream outFile(filePath);

    if (!outFile.is_open()) {
        std::cerr << "Error opening file for writing." << std::endl;
        return 1;
    }
    // outFile << "X" << " " << "Y" << " " << "W" << "\n";
    // Write graph data to the file
    for (const auto& key_value : graph) {
        if ((MODE != Positive_Exact) || key_value.second > 0)
            if ((MODE != All) && NO_WEIGHTS)
                outFile << key_value.first.first << " " << key_value.first.second;
            else
                outFile << key_value.first.first << " " << key_value.first.second << " " << key_value.second << "\n";
    }

    // Close the file
    outFile.close();

    std::cout << "Graph data saved to: " << filePath << std::endl;
    // Rest of the main function logic
    return 0;
}

// Run program: Ctrl + F5 or Debug > Start Without Debugging menu
// Debug program: F5 or Debug > Start Debugging menu

// Tips for Getting Started: 
//   1. Use the Solution Explorer window to add/manage files
//   2. Use the Team Explorer window to connect to source control
//   3. Use the Output window to see build output and other messages
//   4. Use the Error List window to view errors
//   5. Go to Project > Add New Item to create new code files, or Project > Add Existing Item to add existing code files to the project
//   6. In the future, to open this project again, go to File > Open > Project and select the .sln file
