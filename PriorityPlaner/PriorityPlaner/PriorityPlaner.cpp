#include<iostream>
#include<string>
#include<fstream>
#include<vector>
#include<tuple>
#include<chrono>

#include"Utils.h"
#include"Controller.h"
#include"ModelView.h"


using namespace std;

int main(int argc, char** argv) 
{
    //auto start = chrono::steady_clock::now();

    //Argument contorl
    if ( !(2 <= argc && argc <= 4) )
    {
        std::cout << "Incorect number of arguments" << std::endl;
        Help::help_call();
        return 1;
    }

    //help
    if ( argc==2 && argv[1] == Help::help_option)
    {
        Help::help();
        return 0;
    }

    ifstream input(argv[1]);

    //file
    if (!input.is_open())
    {
        std::cout << "File not found" << std::endl;
        Help::help_call();
        return 1;
    }

    //iter
    size_t interations = Model::default_iterations;
    if (argc > 2)
    {
        try
        {
            interations = stoul(argv[2]);
        }
        catch (const std::exception&)
        {
            std::cout << "Invalid argumet for [iterations]" << std::endl;
            Help::help_call();
            return 1;
        }
    }

    //depth
    size_t depth = Model::default_depth;
    if (argc > 3)
    {
        try
        {
            depth = stoul(argv[3]);
        }
        catch (const std::exception&)
        {
            std::cout << "Invalid argumet for [depth]" << std::endl;
            Help::help_call();
            return 1;
        }
    }


    //planner
    Controller c;
    auto [valid,planer] = c.load_data(input);

    input.close();

    //Controller c;
    //auto [valid, planer] = c.load_data(cin);


    if (valid)
    {
        Model m(planer,interations,depth);
        m.Calculate();

        View view;
        view.print_timeline(m, cout);
    }
    else
    {
        std::cout << "Invalid Input" << std::endl;
        return 1;
    }

    //auto end = chrono::steady_clock::now();
    //cout << "Elapsed time in seconds: "
    //    << chrono::duration_cast<chrono::seconds>(end - start).count()
    //    << " sec";
}
