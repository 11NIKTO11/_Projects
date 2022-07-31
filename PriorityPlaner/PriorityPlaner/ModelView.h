#pragma once
#include<algorithm>
#include<vector>
#include<unordered_set>
#include<stdlib.h>
#include"Utils.h"

using namespace std;
class Model
{
public:
    using TimeLine = vector<ActivityPlan>;
    friend class View;

    const static size_t default_iterations = 10000;
    const static size_t default_depth = 1000;
private:
    using timeline_value_t = long long;

    const PlanningData& planning_data;

    Graph<string, TimeData>::GraphDistances distances;

    const size_t iterations;
    const size_t depth;
    const size_t elite; //setted in constructor

    const size_t odds = 100;
    const size_t odds_of_duration = 20;
    const size_t odds_of_adding = 5;
    const size_t odds_of_removing = 5;
    const size_t odds_of_swaping = 10;

    struct TimeLineData
    {
        TimeLine timeline;
        vector<size_t> unused;
        timeline_value_t value = 0;
    };

    vector<TimeLineData> plans;


    bool chance(size_t odds_) const;

    bool is_mandatory(size_t activity_idx) const;

    void swap_activity(TimeLineData& plan) const;
    
    void add_activity(TimeLineData& plan) const;
    
    void remove_activity(TimeLineData& plan) const;
    
    void change_activity_duration(ActivityPlan& plan_activity) const;

    void change_timeline(TimeLineData& plan) const;

    bool rule_check(const TimeLine& timeline) const;

    timeline_value_t evaluate_timeline(const TimeLine& timeline, bool check_mandatory = true) const;

    void mandatory_recursion(TimeLine& timeline, size_t from_index, vector<ActivityPlan>& to_use);

    void find_mandatory_plan();

    void initialize_unused();

    void fill_plans();

    void evolution();

public:

    Model(const PlanningData& planning_data_, size_t iterations = default_iterations, size_t depth = default_depth);

    /// <summary>
    /// Calculates best Timetable
    /// </summary>
    void Calculate();

    Model& operator= (const Model&) = delete;
};

class View
{
public:
    /// <summary>
    /// Prints best timedable from model
    /// </summary>
    void print_timeline(const Model& model, ostream& output) const;
};