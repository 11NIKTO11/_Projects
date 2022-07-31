 #pragma once
#include<string>
#include<iostream>
#include<vector>
#include<unordered_map>
#include<unordered_set>
#include<optional>
#include<iomanip>

using namespace std;


struct TimeData
{
public:
    using time_data_t = int;
private:


    static const time_data_t minute_max = 60;
    static const time_data_t hour_max = 24;
    static const time_data_t day_max = 7;

    time_data_t total_minutes_;

public:
    static TimeData max();

    TimeData();

    TimeData(int total_minutes_);

    TimeData(time_data_t day, time_data_t hour, time_data_t minute);

    time_data_t minute() const;

    time_data_t hour() const;

    time_data_t day() const;

    void set_minute(time_data_t value);

    void set_hour(time_data_t value);

    void set_day(time_data_t value);

    int total_minutes() const;


    TimeData& operator+=(const TimeData& rhs);

    TimeData& operator+=(const int& rhs);

    TimeData& operator-=(const TimeData& rhs);

    TimeData& operator-=(const int& rhs);


    friend TimeData operator+(TimeData lhs, const TimeData& rhs);

    friend TimeData operator+(TimeData lhs, const int& rhs);

    friend TimeData operator-(TimeData lhs, const TimeData& rhs);

    friend TimeData operator-(TimeData lhs, const int& rhs);

    friend std::ostream& operator<<(std::ostream& s, const TimeData& time);

    friend inline bool operator< (const TimeData& lhs, const TimeData& rhs) {
        return lhs.total_minutes_ < rhs.total_minutes_;
    }

    friend inline bool operator> (const TimeData& lhs, const TimeData& rhs) { return rhs < lhs; }

    friend inline bool operator<=(const TimeData& lhs, const TimeData& rhs) { return !(lhs > rhs); }

    friend inline bool operator>=(const TimeData& lhs, const TimeData& rhs) { return !(lhs < rhs); }
};

struct ActivityPlan
{
    size_t activity_idx;
    TimeData duration;
    ActivityPlan(size_t activity_idx_, TimeData duration_);
};

template<typename Key, typename Value>
class IndexedUnorderedMap
{
    using key_value = pair<Key, Value>;
    unordered_map<Key, size_t> index_maping;
    vector<key_value> values;

public:
    size_t size() const 
    {
        return values.size();
    }

    tuple<bool,size_t> emplace(const Key& key, const Value& value)
    {
        auto it = index_maping.find(key);
        if (it == index_maping.end())
        {
            auto idx = size();
            index_maping.emplace( key, idx);
            values.push_back(key_value( key, value));
            return tuple<bool, size_t>(true,idx);
        }
        else
        {
            return tuple<bool, size_t>(false, it->second);
        }
    }

    optional<size_t> get_index(const Key& key) const
    {
        auto it = index_maping.find(key);
        return it != index_maping.end() ? optional<size_t>(it->second) : optional<size_t>();
    }

    tuple<bool,const key_value&> find(const Key& key) const
    {
        auto it = index_maping.find(key);
        if (it != index_maping.end())
        {
            return tuple<bool, const key_value&>(true,at(it->second));
        }
        return tuple<bool, const key_value&>(false, key_value());
    }

    const key_value& at(size_t index) const
    {
        return values.at(index);
    }

    bool erase(const Key& key)
    {
        auto it = index_maping.find(key);
        return it != index_maping.end() ? erase(it->second) : false;

    }

    bool erase(size_t index)
    {
        if (index<size())
        {
            values.erase(values.begin() + index);
            for (size_t i = index; i < size(); i++)
            {
                index_maping.find(values.at(i).first).second = i;
            }
            return true;
        }
        return false;
    }

};

template<typename Node, typename Distance>
class Graph
{
    unordered_map<Node, size_t> nodes;
    vector<unordered_map<size_t, Distance>> edges;

public:
    class GraphDistances
    {
        //using path = pair<optional<Distance>, vector<size_t>>;
        using path = optional<Distance>;
        vector<vector<path>> distances;

        void InitializeProperties(const Graph<Node, Distance>& graph)
        {
            for (size_t from_ = 0; from_ < graph.nodes.size(); from_++)
            {
                for (size_t to_ = 0; to_ < graph.nodes.size(); to_++)
                {
                    auto edge = graph.edges.at(from_).find(to_);
                    if (from_ == to_)
                    {
                        distances.at(from_).push_back(optional<Distance>(Distance(0)));
                    }
                    else if (edge == graph.edges.at(from_).end())
                    {
                        distances.at(from_).push_back(optional<Distance>());
                    }
                    else
                    {
                        distances.at(from_).push_back(optional<Distance>(edge->second));
                    }
                }
            }
        }

        void FloydWarshal(const Graph<Node, Distance>& graph)
        {

            for (size_t node = 0; node < graph.nodes.size(); node++)
            {
                for (size_t from = 0; from < graph.nodes.size(); from++)
                {
                    for (size_t to = 0; to < graph.nodes.size(); to++)
                    {
                        auto edge_without_node = distances.at(from).at(to);
                        auto edge_to_node = distances.at(from).at(node);
                        auto edge_from_node = distances.at(node).at(to);
                        if (edge_to_node.has_value() &&
                            edge_from_node.has_value())
                        {
                            if (!(
                                edge_without_node.has_value() &&
                                edge_without_node.value() <= (edge_to_node.value() + edge_from_node.value())
                                ))
                            {

                                distances.at(from).at(to) = path(edge_to_node.value() + edge_from_node.value());
                            }
                        }
                    }
                }
            }
        }

    public:
        GraphDistances(const Graph<Node, Distance>& graph)
        {
            distances = vector<vector<path>>(graph.nodes.size());

            InitializeProperties(graph);

            FloydWarshal(graph);
        }

        optional<Distance> distance(size_t from_idx, size_t to_idx) const
        {
            if (from_idx < distances.size() &&
                to_idx < distances.size())
            {
                return distances.at(from_idx).at(to_idx);
            }
            else
            {
                return optional<Distance>();
            }
        }
    };

    bool add_node(const Node& new_place)
    {
        if (nodes.find(new_place) == nodes.end())
        {
            nodes.emplace(new_place, nodes.size());
            edges.push_back(unordered_map<size_t, Distance>());
            return true;
        }
        return false;
    }

    bool add_edge(const Node& node_1, const Node& node_2, Distance distance)
    {
        auto from_index = nodes.find(node_1);
        auto to_index = nodes.find(node_2);
        if (from_index == nodes.end() || to_index == nodes.end())
        {
            return false;
        }
        edges.at(from_index->second).emplace(to_index->second, distance);
        edges.at(to_index->second).emplace(from_index->second, distance);
        return true;
    }

    optional<size_t> get_index(const Node& node) const
    {
        auto it = nodes.find(node);
        return it != nodes.end() ? optional<size_t>(it->second) : optional<size_t>();
    }

    optional<Node> get_key(size_t index) const
    {
        for (auto&& node : nodes)
        {
            if (node.second == index)
            {
                return optional<Node>(node.first);
            }
        }
        return optional<Node>();
    }

    GraphDistances calculate_distancies() const
    {
        return GraphDistances(*this);
    }
};

class PlanningData
{
public:

    using priority_t = int;

    struct ActivityData
    {
    public:
        string name;
        size_t place;
        vector<size_t> categories;
        priority_t priority;
        TimeData start_time;
        TimeData end_time;
        TimeData min_duration;
        TimeData max_duration;

        ActivityData();

        ActivityData(
            const string& activity_name,
            size_t activity_palce,
            vector<size_t>&& activity_categories,
            priority_t activity_priority,
            TimeData activity_start_time,
            TimeData activity_end_time,
            TimeData activity_min_duration,
            TimeData activity_max_duration
        );
    };


    const string default_name = "";

    TimeData start_time;

    TimeData end_time;

private:


    size_t staring_location_ = 0;

    IndexedUnorderedMap<string,ActivityData> activities_;

    unordered_set<size_t> mandatory_activities_;

    IndexedUnorderedMap<string, TimeData> categories_;

    Graph<string,TimeData> locations_;

    unordered_map<size_t,unordered_set<size_t>> rules_;

public:

    PlanningData(TimeData start_time_, TimeData end_time_);

    const IndexedUnorderedMap<string, ActivityData>& activities() const;

    const unordered_set<size_t>& mandatory_activities() const;

    const IndexedUnorderedMap<string, TimeData>& categories() const;

    const Graph<string, TimeData>& locations() const;

    size_t staring_location() const;

    bool can_follow(size_t first, size_t next) const;

    bool set_starting_location(const string& location_name);

    bool add_activity(
        const string& activity_name,
        const string& activity_palce,
        const vector<string>& activity_categories,
        priority_t activity_priority,
        TimeData activity_start_time,
        TimeData activity_end_time,
        TimeData activity_min_duration,
        TimeData activity_max_duration);

    bool add_category(const string& category_name, TimeData max_duration);

    bool add_location(const string& new_place);

    bool add_place_distance(const string& from_place, const string& to_place, TimeData distance);

    bool add_rule(const string& activity, const string& activity_next);

    PlanningData& operator= (const PlanningData&) = delete;
};

