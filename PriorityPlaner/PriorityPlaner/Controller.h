#pragma once
/* TIMEFRAME */
/* (start) D:HH:MM; (end) D:HH:MM */
/* PLACES */
/* location_name */
/* DISTANCES */
/* location_name_1, location_name_2, (duration) D:HH:MM */
/* CATEGORIES */
/* category_name;(max_duration) HH:MM */
/* START_LOCATION */
/* location_name */
/* ACTIVITIES */
/* activity_name; place_name; category_name; priority; (start_time) D:HH:MM; (end_time) D:HH:MM; (min_duration) D:HH:MM; (max_duration) D:HH:MM; (duration) D:HH:MM */
/* ACTIVITIES_ORDER */
/* activity_name_1;activity_name_2*/

#include<iostream>
#include<fstream>
#include<sstream>
#include<string>
#include<vector>
#include<tuple>
#include<unordered_map>
#include<filesystem>
#include"Utils.h"
#include"ModelView.h"


using namespace std;


class Help
{

public:
    const static string help_option;

    static void help();

    static void help_call();

};

class Controller
{
private:

    enum class Sections
    {
        TIMEFRAME,
        //PERSON,
        PLACES,
        DISTANCES,
        CATEGORIES,
        STAR_LOCATIONT,
        ACTIVITIES,
        ACTIVITIES_ORDER
    };

    enum class Errors
    {
        ARGUMENT_NUMBER,
        DATA,
        TIME,
        SECTION,
        PRIORITY
    };


    struct SectionInfo
    {
        Sections section;
        size_t arguments_count;
      
        SectionInfo(Sections section_, size_t arguments_count_);
    };

    const unordered_map<string,SectionInfo> sections = 
    unordered_map<string, SectionInfo>({
        {"TIMEFRAME",       SectionInfo(Sections::TIMEFRAME,2)},
        {"PLACES",          SectionInfo(Sections::PLACES,1)},
        {"DISTANCES",       SectionInfo(Sections::DISTANCES,3)},
        {"CATEGORIES",      SectionInfo(Sections::CATEGORIES,2)},
        {"START_LOCATION",  SectionInfo(Sections::STAR_LOCATIONT,1)},
        {"ACTIVITIES",      SectionInfo(Sections::ACTIVITIES,8)},
        {"ACTIVITIES_ORDER",SectionInfo(Sections::ACTIVITIES_ORDER,2)}
    });

    const string max = "max";

    const char delimiter_data = ';';
    const char delimiter_time = ':';
    const char delimiter_category = ',';


    size_t line_number = 0;
    bool correct_data = true;

    vector<string> line_parser(const string& line, const char delimiter_) const;

    PlanningData::priority_t get_priority(const string& priority_str);
    TimeData get_time(const string& time_str);
    void report_error(Errors type);

public:
    /// <summary>
    /// Loads data from input to PlanningData, false if Data are ivalid
    /// </summary>
    /// <param name="input"></param>
    /// <returns></returns>
    tuple<bool, PlanningData> load_data(istream& input);

    Controller& operator= (const Controller&) = delete;
};

