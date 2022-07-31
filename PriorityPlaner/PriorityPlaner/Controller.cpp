#include"Controller.h"

const string Help::help_option = "--help";

void Help::help()
{
    std::cout << "Calculates plan based on provided file. Program uses Evolutionary algorithm." << std::endl;
    std::cout << std::endl;
    std::cout << "  priorityplanner.exe file_name [iterations] [depth]" << std::endl;
    std::cout << std::endl;
    std::cout << "Arguments: " << std::endl;
    std::cout << "  file_name - Provide full or relativ path to the file with activities" << std::endl;
    std::cout << "  [iterations] - Number of iterations in algorithm. Value must fit size_t and be greather than zero. Default value is " << Model::default_iterations << "." << std::endl;
    std::cout << "  [depth] - Population size in algorithm. Value must fit size_t and be greather than zero. Default value is " << Model::default_depth << "." << std::endl;
    std::cout << std::endl;
    std::cout << "Program working directory: " << std::filesystem::current_path().string() << std::endl;
    std::cout << std::endl;
}

void Help::help_call()
{
    std::cout << "Call : \"priorityplanner.exe " << Help::help_option << "\" for more information" << std::endl;
}


Controller::SectionInfo::SectionInfo(Sections section_, size_t arguments_count_)
    :section(section_),arguments_count(arguments_count_) {}

void Controller::report_error(Errors type) 
{
    correct_data = false;
    cout << "On line " << line_number << " - ";
    switch (type)
    {
    case Errors::ARGUMENT_NUMBER:
        cout << "Incorrect number of data";
        break;
    case Errors::DATA:
        cout << "Invalid data";
        break;
    case Errors::TIME:
        cout << "Invalid time format";
        break;
    case Errors::SECTION:
        cout << "Section not setted";
        break;
    case Errors::PRIORITY:
        cout << "Invalid priority value";
        break;
    default:
        cout << "Unrecognized error";
        break;
    }
    cout << endl;
}

TimeData Controller::get_time(const string& time_str)
{
    auto time_data = line_parser(time_str, delimiter_time);
    TimeData time(0);
    try
    {
        time = TimeData(
            stoi(time_data.at(0)),
            stoi(time_data.at(1)),
            stoi(time_data.at(2))
        );
    }
    catch (const exception&)
    {
        report_error(Errors::TIME);
    }
    return time;
}

PlanningData::priority_t Controller::get_priority(const string& priority_str)
{
    PlanningData::priority_t priority= 0;
    try
    {
        priority = stoi(priority_str);
    }
    catch (const exception&)
    {
        report_error(Errors::PRIORITY);
    }
    return priority;
}

vector<string> Controller::line_parser(const string& line, const char delimiter_) const
{
    vector<string> value;
    size_t pos_begin = 0;
    while (pos_begin != string::npos)
    {
        size_t pos_end = line.find(delimiter_, pos_begin);
        value.push_back(line.substr(pos_begin, pos_end - pos_begin));
        if (pos_end == string::npos)
        {
            pos_begin = pos_end;
        }
        else
        {
            pos_begin = pos_end + 1;
        }
    }
    return value;
}

tuple<bool, PlanningData> Controller::load_data(istream& input)
{

    PlanningData data(TimeData(0), TimeData::max());
    bool timeframe = false;
    bool starting_location = true;
    correct_data = true;

    string line;
    line_number = 0;
    auto section = sections.end();
    
    while ( !input.eof() && !input.bad())
    {
        getline(input, line);
        line_number++;

        if (!line.empty())
        {
            auto new_section = sections.find(line);
            //section switch
            if (new_section != sections.end())
            {
                section = new_section;
            }
            //adding data
            else
            {
                if (section == sections.end())
                {
                    report_error(Errors::SECTION);
                }
                else
                {
                    auto line_data = line_parser(line,delimiter_data);
                    bool data_added = false;

                    if (line_data.size() != section->second.arguments_count)
                    {
                        report_error(Errors::ARGUMENT_NUMBER);
                    }
                    else
                    {
                        switch (section->second.section)
                        {
                            case Sections::TIMEFRAME:
                                data.start_time = get_time(line_data.at(0));
                                data.end_time = get_time(line_data.at(1));
                                timeframe = true;
                                data_added = true;
                                break;
                            case Sections::PLACES:
                                data_added = data.add_location(line_data.at(0));
                                starting_location = false;
                                break;
                            case Sections::DISTANCES:
                                data_added = data.add_place_distance(line_data.at(0), line_data.at(1), get_time(line_data.at(2)));
                                break;
                            case Sections::CATEGORIES:
                                data_added = data.add_category(line_data.at(0), get_time(line_data.at(1)));
                                break;
                            case Sections::STAR_LOCATIONT:
                                data_added = data.set_starting_location(line_data.at(0));
                                starting_location = true;
                                break;
                            case Sections::ACTIVITIES:
                                data_added = data.add_activity(
                                    line_data.at(0),
                                    line_data.at(1).empty() ? data.default_name : line_data.at(1),
                                    line_data.at(2).empty() ? vector<string>() : line_parser( line_data.at(2), delimiter_category),
                                    line_data.at(3) == max ? std::numeric_limits<int>::max() : get_priority(line_data.at(3)),
                                    get_time(line_data.at(4)),
                                    get_time(line_data.at(5)),
                                    get_time(line_data.at(6)),
                                    get_time(line_data.at(7)));
                                break;
                            case Sections::ACTIVITIES_ORDER:
                                data_added = data.add_rule(line_data.at(0), line_data.at(1));
                                break;
                            default:
                                break;
                        }

                        if (!data_added)
                        {
                            report_error(Errors::DATA);
                        }
                    }
                }
            }
        }
    }

    //warning report
    if (!timeframe)
    {
        cout << "Warning: Timeframe not setted, default timeframe will be used" << endl;
    }
    if (!starting_location)
    {
        cout << "Warning: Starting location not setted, default starting location will be used" << endl;
    }

    return tuple<bool, PlanningData>(correct_data,data);
}