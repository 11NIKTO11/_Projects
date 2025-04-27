//// Graph.cpp : This file contains the 'main' function. Program execution begins and ends there.
////
//
//#include <iostream>
//#include <fstream>
//#include <sstream>
//#include <vector>
//#include <map>
//#include <ctime>
//#include <filesystem>
//#include <deque>
//
//namespace {
//    const int MAX_COLOR = 32;
//    const int HISTORY_LENGHT = 3;
//    const std::string PATH = "..\\..\\";
//    const bool ONLY_POSITIVE = true;
//    const bool NO_WEIGHTS = false;
//}
//
//struct PixelPlacementInfo {
//    int user_id_num;
//    double time;
//    int X, Y, color;
//
//    std::string toString() const {
//        std::ostringstream oss;
//        oss << X << " " << Y << " " << user_id_num << " " << color << " " << time;
//        return oss.str();
//    }
//};
//
//std::string getCurrentTime() {
//    std::time_t now = std::time(0);
//    struct tm timeinfo;
//    char buffer[80];
//    time(&now);
//    localtime_s(&timeinfo, &now);
//    strftime(buffer, sizeof(buffer), "%d-%m-%Y %H:%M:%S", &timeinfo);
//    return std::string(buffer);
//}
//
//void readColorDistanceWeight(double color_distance_weight[][MAX_COLOR]) {
//    std::ifstream file(PATH + "color_distance_weight.txt");
//    for (int i = 0; i < MAX_COLOR; ++i) {
//        for (int j = 0; j < MAX_COLOR; ++j) {
//            file >> color_distance_weight[i][j];
//        }
//    }
//    file.close();
//}
//
//std::map<int, std::map<int, int>> readAndProcessData(int N, double color_distance_weight[][MAX_COLOR]) {
//    std::map<int, std::map<int, int>> graph;
//    std::ifstream file(PATH + "2022_place_canvas_history_grouped.csv");
//    std::string line;
//    std::deque<PixelPlacementInfo> recordsHistory;
//    std::getline(file, line);
//    int c = 0;
//    while (std::getline(file, line)) {
//
//        if (c % 10000000 == 0) {
//            std::cout << c << " " << getCurrentTime() << std::endl;
//        }
//
//        //if (c == 10000000) {
//        //    break;
//        //}
//        c++;
//
//        std::istringstream iss(line);
//        std::string token;
//
//        // Assuming CSV structure and adjust the parsing accordingly
//        PixelPlacementInfo pixelInfo;
//
//        // Read tokens separated by commas
//        std::getline(iss, token, ','); // user_id_num
//        pixelInfo.user_id_num = std::stoi(token);
//
//        std::getline(iss, token, ','); // time
//        pixelInfo.time = std::stod(token);
//
//        std::getline(iss, token, ','); // X
//        pixelInfo.X = std::stoi(token);
//
//        std::getline(iss, token, ','); // Y
//        pixelInfo.Y = std::stoi(token);
//
//        std::getline(iss, token, ','); // color
//        pixelInfo.color = std::stoi(token);
//
//
//        // Keep only the last 5 records in the list
//        if (recordsHistory.size() > HISTORY_LENGHT) {
//            recordsHistory.pop_front();
//        }
//
//        while (!recordsHistory.empty() && (pixelInfo.X != recordsHistory.front().X || pixelInfo.Y != recordsHistory.front().Y)) {
//            recordsHistory.pop_front();
//        }
//
//        // Print the last 5 records
//        for (const auto& record : recordsHistory) {
//            // std::cout << pixelInfo.toString() << " - " << record.toString() << " weight: " << color_distance_weight[pixelInfo.color][record.color] << "\n";
//            auto w = color_distance_weight[pixelInfo.color][record.color];
//            if ((not ONLY_POSITIVE) || w > 0)
//            {
//                int e1, e2;
//                if (pixelInfo.user_id_num > record.user_id_num) {
//                    e1 = record.user_id_num;
//                    e2 = pixelInfo.user_id_num;
//                }
//                else {
//                    e1 = pixelInfo.user_id_num;
//                    e2 = record.user_id_num;
//                }
//
//                auto it_outer = graph.find(e1);
//
//                if (it_outer != graph.end()) {
//                    // e1 exists, check if e2 exists in the inner map
//                    auto it_inner = it_outer->second.find(e2);
//
//                    if (it_inner != it_outer->second.end()) {
//                        // e2 exists, add w to the existing value
//                        it_inner->second += w;
//                    }
//                    else {
//                        // e2 doesn't exist, set the value to w
//                        it_outer->second[e2] = w;
//                    }
//                }
//                else {
//                    // e1 doesn't exist, create a new entry with e2 and w
//                    graph[e1][e2] = w;
//                }
//
//            }
//
//        }
//
//        recordsHistory.push_back(pixelInfo);
//
//        /*for (int i = 0; i < graph[X][Y].size(); ++i) {
//            if (c % 1000000 == 0) {
//                std::cout << c << " " << getCurrentTime() << std::endl;
//            }
//            c++;
//
//            PixelInfo n = graph[X][Y][i];
//            for (int j = std::max(-5, -i); j < 0; ++j) {
//                PixelInfo m = graph[X][Y][i + j];
//                int w = color_distance_weight[n.color][m.color];
//                if (G.has_edge(n.user_id_num, m.user_id_num)) {
//                    G[n.user_id_num][m.user_id_num]['weight'] += w;
//                }
//                else {
//                    G.add_edge(n.user_id_num, m.user_id_num, weight = w);
//                }
//            }
//        }*/
//    }
//    file.close();
//
//    return graph;
//}
//
//int main() {
//    //std::filesystem::path currentPath = std::filesystem::current_path();
//    //std::cout << "Current Working Directory: " << currentPath << std::endl;
//    const int N = 10; // Adjust the value of N accordingly
//    double color_distance_weight[MAX_COLOR][MAX_COLOR]; // Initialize this array accordingly
//    readColorDistanceWeight(color_distance_weight);
//    std::map<int, std::map<int, int>> graph = readAndProcessData(N, color_distance_weight);
//    const std::string filePath = PATH + "edge_lists\\2022_graph_weighted_edges_" + (ONLY_POSITIVE ? "positive_" : "") + std::to_string(HISTORY_LENGHT) + ".txt";
//    // Open the file for writing
//    std::ofstream outFile(filePath);
//
//    if (!outFile.is_open()) {
//        std::cerr << "Error opening file for writing." << std::endl;
//        return 1;
//    }
//    // outFile << "X" << " " << "Y" << " " << "W" << "\n";
//    // Write graph data to the file
//    for (const auto& outer : graph) {
//        for (const auto& inner : outer.second) {
//            if (NO_WEIGHTS && ONLY_POSITIVE)
//                outFile << outer.first << " " << inner.first;
//            else
//                if ((not ONLY_POSITIVE) || inner.second > 0)
//                    outFile << outer.first << " " << inner.first << " " << inner.second << "\n";
//        }
//    }
//
//    // Close the file
//    outFile.close();
//
//    std::cout << "Graph data saved to: " << filePath << std::endl;
//    // Rest of the main function logic
//    return 0;
//}
//
//// Run program: Ctrl + F5 or Debug > Start Without Debugging menu
//// Debug program: F5 or Debug > Start Debugging menu
//
//// Tips for Getting Started: 
////   1. Use the Solution Explorer window to add/manage files
////   2. Use the Team Explorer window to connect to source control
////   3. Use the Output window to see build output and other messages
////   4. Use the Error List window to view errors
////   5. Go to Project > Add New Item to create new code files, or Project > Add Existing Item to add existing code files to the project
////   6. In the future, to open this project again, go to File > Open > Project and select the .sln file
