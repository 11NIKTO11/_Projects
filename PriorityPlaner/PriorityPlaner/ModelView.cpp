#include"ModelView.h"

Model::Model(const PlanningData& planning_data_, size_t iterations_, size_t depth_)
    :planning_data(planning_data_),
    distances(planning_data_.locations().calculate_distancies()),
    iterations(iterations_ == 0 ? default_iterations:iterations_),
    depth(depth_ == 0 ? default_depth : depth_),
    elite(depth / 4)
{}

bool Model::is_mandatory(size_t activity_idx) const
{
    return 
        planning_data.mandatory_activities().find(activity_idx) !=
        planning_data.mandatory_activities().end();
}

bool Model::chance(size_t odds_) const
{
    return odds_ > rand() % odds;
}

void Model::swap_activity(TimeLineData& plan) const
{
    if (plan.timeline.size() > 1 && chance(odds_of_swaping))
    {
        size_t index_1 = rand() % plan.timeline.size();
        size_t index_2 = rand() % plan.timeline.size();
        auto tmp = plan.timeline[index_1];
        plan.timeline[index_1] = plan.timeline[index_2];
        plan.timeline[index_2] = tmp;
    }
}

void Model::add_activity(TimeLineData& plan) const
{
    if (!plan.unused.empty() && chance(odds_of_adding))
    {
        auto insertion_position = plan.timeline.begin() + (const int)(rand() % (plan.timeline.size() + 1));
        auto to_add = plan.unused.begin() + (const int)(rand() % plan.unused.size());
        plan.timeline.insert(insertion_position,
            ActivityPlan(*to_add, planning_data.activities().at(*to_add).second.min_duration)
        );
        plan.unused.erase(to_add);
    }
}

void Model::remove_activity(TimeLineData& plan) const
{
    if (!plan.timeline.empty() && chance(odds_of_removing))
    {
        auto remove_at = plan.timeline.begin() + (const int)(rand() % (plan.timeline.size()));
        if (!is_mandatory(remove_at->activity_idx))
        {
            plan.unused.push_back(remove_at->activity_idx);
            plan.timeline.erase(remove_at);
        }
    }
}

void Model::change_activity_duration(ActivityPlan& plan_activity) const
{
    if (chance(odds_of_duration))
    {
        const PlanningData::ActivityData& activity = planning_data.activities().at(plan_activity.activity_idx).second;
        //auto one = chance(odds / 2) ? +1 : -1; //positive/negative change
        //plan.timeline[index].duration += one*(rand()%10); 
        if (activity.min_duration < activity.max_duration)
        {
            plan_activity.duration = activity.min_duration +
                (rand() % (activity.max_duration.total_minutes() - activity.min_duration.total_minutes()));
        }
    }
}

void Model::change_timeline(TimeLineData& plan) const
{
    swap_activity(plan);
    add_activity(plan);
    remove_activity(plan);
    for (auto&& plan_activity:plan.timeline)
    {
        change_activity_duration(plan_activity);
    }

}

bool Model::rule_check(const Model::TimeLine& timeline) const
{
    for (size_t i = 1; i < timeline.size(); i++)
    {
        if (!planning_data.can_follow(timeline[i-1].activity_idx, timeline[i].activity_idx))
        {
            return false;
        }
    }
    return true;
}

Model::timeline_value_t Model::evaluate_timeline(const Model::TimeLine& timeline, bool check_mandatory) const
{
    timeline_value_t zero_value = 0;
    timeline_value_t value = 0;
    size_t mandatory_count = 0;
    size_t last_location = planning_data.staring_location();
    TimeData last_activity_time(planning_data.start_time);
    vector<TimeData> categories_times = vector<TimeData>(planning_data.categories().size());

    if (!rule_check(timeline))
    {
        return zero_value;
    }

    //timetable construction;
    for (auto&& activity_plan : timeline)
    {
        const PlanningData::ActivityData& activity = planning_data.activities().at(activity_plan.activity_idx).second;
        if (activity.min_duration <= activity_plan.duration &&
            activity.max_duration >= activity_plan.duration)
        {
            //location check
            if (last_location != activity.place)
            {
                auto distance = distances.distance(last_location, activity.place);
                if (distance.has_value())
                {
                    last_activity_time += distance.value();
                    last_location = activity.place;

                }
                else
                {
                    return zero_value;
                }
            }

            //add activity
            last_activity_time = max(last_activity_time, activity.start_time) + activity_plan.duration;
            if (last_activity_time <= activity.end_time)
            {
                if (is_mandatory(activity_plan.activity_idx))
                {
                    mandatory_count++;
                    value += activity.priority;
                }
                else
                {
                    value += (activity.priority*activity_plan.duration.total_minutes()) / activity.max_duration.total_minutes();
                }
                for (auto&& category: activity.categories)
                {
                    categories_times.at(category) += activity_plan.duration;
                }
            }
            else
            {
                return zero_value;
            }
        }
        else
        {
            return zero_value;
        }
    }

    //end time chceck
    if (last_activity_time > planning_data.end_time)
    {
        return zero_value;
    }


    //all mandatory activities are used
    if (check_mandatory && mandatory_count != planning_data.mandatory_activities().size())
    {
        return zero_value;
    }

    //categorie check
    for (size_t i = 0; i < planning_data.categories().size(); i++)
    {
        if (categories_times.at(i) > planning_data.categories().at(i).second)
        {
            return zero_value;
        }
    }

    return value;
}

void Model::mandatory_recursion( TimeLine& timeline, size_t from_index, vector<ActivityPlan>& to_use)
{
    if (to_use.empty())
    {
        plans.push_back(TimeLineData());
        plans.back().timeline = timeline;
        return;
    }
    for (size_t add_activity = 0; add_activity < to_use.size(); add_activity++)
    {
        for (size_t insert_position = from_index; insert_position <= timeline.size(); insert_position++)
        {
            auto activity = to_use.at(add_activity);
            timeline.insert(timeline.begin() + (const int)insert_position, activity);
            if (evaluate_timeline(timeline, false) > 0)
            {
                to_use.erase(to_use.begin() + (const int)add_activity);
                mandatory_recursion(timeline, insert_position + 1, to_use);
                to_use.insert(to_use.begin() + (const int)add_activity, activity);
            }
            timeline.erase(timeline.begin() + (const int)insert_position);
            if (!(depth > plans.size()))
            {
                //we have enoughtmandatorytimelinest
                return;
            }
        }
    }
}

void Model::find_mandatory_plan()
{
    TimeLine mandatory_plan;

    //minimal lenghts of mandatory activities
    for (auto&& activity : planning_data.mandatory_activities())
    {
        mandatory_plan.push_back(ActivityPlan(activity, planning_data.activities().at(activity).second.min_duration));
    }

    //sort by start time
    sort(mandatory_plan.begin(), mandatory_plan.end(),
        [this](const ActivityPlan& lhs, const ActivityPlan& rhs)
        {
            return
                planning_data.activities().at(lhs.activity_idx).second.start_time <
                planning_data.activities().at(rhs.activity_idx).second.start_time;
        }
    );

    //index at i has value of 
    //index of first element in sorted mandatory plan whose starting time si more than i's ending time or
    //mandatory_plan.size() if there is none
    vector<size_t> after_idx;
    for (auto begin = mandatory_plan.begin(), end = mandatory_plan.end(); begin != end; ++begin)
    {
        auto end_time = planning_data.activities().at(begin->activity_idx).second.end_time;
        auto it = find_if(begin, mandatory_plan.end(),
            [this, end_time](const ActivityPlan& act)
            {
                return end_time <= planning_data.activities().at(act.activity_idx).second.start_time;
            }
        );
        after_idx.push_back((size_t)(it - mandatory_plan.begin()));
    }


    //basic plan
    TimeLine basic_mandatory_plan;
    vector<ActivityPlan> unused_mandatory;
    size_t plan_idx = 0;
    for (size_t i = 0; i <= mandatory_plan.size(); i++)
    {
        if (i < after_idx[plan_idx])
        {
            if (after_idx[i] < after_idx[plan_idx])
            {
                plan_idx = i;
            }
            else
            {
                if (plan_idx != i)
                {
                    unused_mandatory.push_back(mandatory_plan[i]);
                }
            }
        }
        else if (i == after_idx[plan_idx])
        {
            basic_mandatory_plan.push_back(mandatory_plan[plan_idx]);
            plan_idx = i;
        }
        else
        {
            throw logic_error("not planed index");
        }

    }

    mandatory_recursion(basic_mandatory_plan, 0, unused_mandatory);
}

void Model::initialize_unused()
{
    vector<size_t> nonmandatory_activities;
    for (size_t activity_idx = 0; activity_idx < planning_data.activities().size(); activity_idx++)
    {
        if (!is_mandatory(activity_idx))
        {
            nonmandatory_activities.push_back(activity_idx);
        }
    }

    for (auto&& plan : plans)
    {
        plan.unused = nonmandatory_activities;
    }
}

void Model::fill_plans()
{
    size_t initial = 0;
    while (plans.size() < depth)
    {
        plans.push_back(plans[initial]);
    }
}

void Model::evolution()
{
    //mutation
    for (auto begin = plans.begin() + (const int)elite, end = plans.end(); begin != end; ++begin)
    {
        auto& plan = *begin;
        change_timeline(plan);
        plan.value = evaluate_timeline(plan.timeline);
    }

    sort(plans.begin(), plans.end(),
        [](const TimeLineData& lhs, const TimeLineData& rhs)
        {
            return lhs.value > rhs.value;
        }
    );

    //selection & repopulation
    size_t to_replicate = 0;
    size_t to_execute = plans.size() - elite;
    while (plans.size() > to_execute)
    {
        plans[to_execute] = plans[to_replicate];
        to_execute++;
        to_replicate++;
    }
}

void Model::Calculate()
{
    if (planning_data.mandatory_activities().empty())
    {
        plans.push_back(TimeLineData());
    }
    else
    {
        find_mandatory_plan();
    }

    if (plans.empty())
    {
        return;
    }

    initialize_unused();

    fill_plans();

    //Evolution
    for (size_t iteration = 0; iteration < iterations; iteration++)
    {
        evolution();
    }
}

void View::print_timeline(const Model& model, ostream& output) const
{
    if (model.plans.empty() || model.plans.at(0).value==0)
    {
        output << "No valid timeline."<< endl;
        return;
    }

    auto& timeline = model.plans.at(0).timeline;
    size_t last_location = model.planning_data.staring_location();
    TimeData last_activity_time(model.planning_data.start_time);
    for (auto&& activity_plan : timeline)
    {
        const PlanningData::ActivityData& activity = model.planning_data.activities().at(activity_plan.activity_idx).second;

        //location check
        if (last_location != activity.place)
        {
            auto distance = model.distances.distance(last_location, activity.place);
            if (distance.has_value())
            {
                output << "Travel from " << model.planning_data.locations().get_key(last_location).value();
                last_location = activity.place;
                output << " to " << model.planning_data.locations().get_key(last_location).value() << std::endl;

                output << last_activity_time << " - ";
                last_activity_time += distance.value();
                output << last_activity_time << std::endl;
            }
            else
            {
                output << "Cannot travel from " << model.planning_data.locations().get_key(last_location).value();
                last_location = activity.place;
                output << " to " << model.planning_data.locations().get_key(last_location).value() << std::endl;
                return;
            }
        }

        auto start_time = max(last_activity_time, activity.start_time);
        last_activity_time = start_time + activity_plan.duration;

        output << "Time for " << activity.name;
        if (!activity.categories.empty())
        {
            output << " from ";
            (activity.categories.size() == 1) ? output << "category " : output << " categories ";
        }
        for (size_t i = 0; i < activity.categories.size(); i++)
        {
            if (i > 0)
            {
                (i < activity.categories.size() - 1) ? output << ", " : output << " and ";
            }
            output << model.planning_data.categories().at(activity.categories[i]).first;

        }
        output << std::endl;
        output << start_time << " - " << last_activity_time << std::endl;
    }
}
