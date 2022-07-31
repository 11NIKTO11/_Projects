#include"Utils.h"

#pragma region TimeData

TimeData TimeData::max()
{
    TimeData t(0);
    t.total_minutes_ = minute_max * hour_max * day_max - 1;
    return t;
}


TimeData::TimeData() : total_minutes_(0) {}

TimeData::TimeData(int total_minutes_) : total_minutes_(total_minutes_%(minute_max*hour_max*day_max)) {}

TimeData::TimeData(time_data_t day, time_data_t hour, time_data_t minute)
    : total_minutes_(0)
{
    set_day(day);
    set_hour(hour);
    set_minute(minute);
}

TimeData::time_data_t TimeData::minute() const
{
    return total_minutes_ % minute_max;
};

TimeData::time_data_t TimeData::hour() const
{
    return (total_minutes_ / minute_max)% hour_max;
}

TimeData::time_data_t TimeData::day() const
{
    return (total_minutes_ / (minute_max* hour_max)) % day_max;
}

void TimeData::set_minute(time_data_t value)
{
    if (value >= minute_max)
    {
        throw invalid_argument("minutes out of range");
    }
    total_minutes_ += value -minute();
}

void TimeData::set_hour(time_data_t value)
{
    if (value >= hour_max)
    {
        throw invalid_argument("hour out of range");
    }
    total_minutes_ += (value - hour())*minute_max;
}

void TimeData::set_day(time_data_t value)
{
    if (value >= hour_max)
    {
        throw invalid_argument("day out of range");
    }
    total_minutes_ += (value - day()) * minute_max*hour_max;
}

int TimeData::total_minutes() const
{
    return total_minutes_;
}

TimeData& TimeData::operator+=(const int& rhs)
{
    total_minutes_ += rhs;
    return *this;
}

TimeData& TimeData::operator-=(const int& rhs)
{
    total_minutes_ -= rhs;
    return *this;
}

TimeData& TimeData::operator+=(const TimeData& rhs)
{
    *this += rhs.total_minutes_;
    return *this;
}

TimeData& TimeData::operator-=(const TimeData& rhs)
{
    *this -= rhs.total_minutes_;
    return *this;
}

TimeData operator+(TimeData lhs, const int& rhs)
{
    lhs += rhs;
    return lhs;
}

TimeData operator-(TimeData lhs, const int& rhs)
{
    lhs -= rhs;
    return lhs;
}

TimeData operator+(TimeData lhs, const TimeData& rhs)
{
    lhs += rhs;
    return lhs;
}

TimeData operator-(TimeData lhs, const TimeData& rhs)
{
    lhs -= rhs;
    return lhs;
}


std::ostream& operator<<(std::ostream& s, const TimeData& time)
{
    s << "day ";
    s << time.day();
    s << " ";
    s << setw(2) << setfill('0') << time.hour();
    s << ":";
    s << setw(2) << setfill('0') << time.minute();
    return (s);
}


#pragma endregion

#pragma region ActivityPlan

ActivityPlan::ActivityPlan(size_t activity_idx_, TimeData duration_)
 : activity_idx(activity_idx_),duration(duration_) {}

#pragma endregion

#pragma region PlanningData


#pragma region ActivityData


PlanningData::ActivityData::ActivityData():
    place(0),
    categories(vector<size_t>()),
    priority(0)
{}

PlanningData::ActivityData::ActivityData(
    const string& activity_name,
    size_t activity_palce,
    vector<size_t>&& activity_categories,
    priority_t activity_priority,
    TimeData activity_start_time,
    TimeData activity_end_time,
    TimeData activity_min_duration,
    TimeData activity_max_duration
) :
    name(activity_name),
    place(activity_palce),
    categories(move(activity_categories)),
    priority(activity_priority),
    start_time(activity_start_time),
    end_time(activity_end_time),
    min_duration(activity_min_duration),
    max_duration(activity_max_duration)
{
    if(activity_start_time > activity_end_time ||
        activity_min_duration > activity_max_duration)
    {
        throw invalid_argument("invalid times");
    }

}

#pragma endregion

PlanningData::PlanningData(TimeData start_time_, TimeData end_time_)
    :start_time(start_time_), end_time(end_time_)
{
    locations_.add_node(default_name);
    categories_.emplace(default_name, 0);
}

const IndexedUnorderedMap<string, PlanningData::ActivityData>& PlanningData::activities() const
{
    return activities_;
}

const unordered_set<size_t>& PlanningData::mandatory_activities() const
{
    return mandatory_activities_;
}

const IndexedUnorderedMap<string, TimeData>& PlanningData::categories() const
{
    return categories_;
}

const Graph<string, TimeData>& PlanningData::locations() const
{
    return locations_;
}

size_t PlanningData::staring_location() const
{
    return staring_location_;
}

bool PlanningData::can_follow(size_t first, size_t next) const
{
    auto it = rules_.find(first);
    return it == rules_.end() ? true : it->second.find(next) == it->second.end();
}


bool PlanningData::add_activity(
    const string& activity_name,
    const string& activity_palce,
    const vector<string>& activity_categories,
    priority_t activity_priority,
    TimeData activity_start_time,
    TimeData activity_end_time,
    TimeData activity_min_duration,
    TimeData activity_max_duration)
{
    auto place = locations_.get_index(activity_palce);

    if ( !place.has_value() )
    {
        return false;
    }

    vector<size_t> categories;

    for (auto&& category:activity_categories)
    {
        auto category_idx = categories_.get_index(category);
        if (category_idx.has_value())
        {
            categories.push_back(category_idx.value());
        }
        else
        {
            return false;
        }
    }


    try
    {
        auto [valid_activity, idx] = activities_.emplace(activity_name, ActivityData(
            activity_name,
            place.value(),
            move(categories),
            activity_priority,
            activity_start_time,
            activity_end_time,
            activity_min_duration,
            activity_max_duration
        ));


        if (!valid_activity)
        {
            return false;
        }

        if (activity_priority == std::numeric_limits<priority_t>::max())
        {
            mandatory_activities_.emplace(idx);
        }
    }
    catch (const std::exception&)
    {
        return false;
    }

    return true;
}

bool PlanningData::add_category(const string& category_name, TimeData max_duration)
{
        auto[success,idx] =categories_.emplace(category_name, max_duration);
        return success;
}

bool PlanningData::add_location(const string& new_place)
{
    return locations_.add_node(new_place);
}

bool PlanningData::add_place_distance(const string& from_place, const string& to_place, TimeData distance)
{
    return locations_.add_edge(from_place, to_place, distance);
}

bool PlanningData::add_rule(const string& activity, const string& activity_next)
{
    auto a_idx =activities_.get_index(activity);
    auto a_next_idx = activities_.get_index(activity_next);
    if (a_idx.has_value() && a_next_idx.has_value())
    {
        auto it = rules_.find(a_idx.value());
        if (it == rules_.end())
        {
            it =rules_.emplace(a_idx.value(), unordered_set<size_t>()).first;
        }
        it->second.insert(a_next_idx.value());
        return true;
    }
    else
    {
        return false;
    }
}

bool PlanningData::set_starting_location(const string& location_name)
{
    auto idx = locations_.get_index(location_name);
    if (idx.has_value())
    {
        staring_location_ = idx.value();
        return true;
    }
    else
    {
        return false;
    }
}

#pragma endregion