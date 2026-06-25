#include <iostream>
#include <fstream>
#include <string>
#include <algorithm>
#include <cctype>
#include <sstream>

#include "json.hpp"

using json = nlohmann::json;
using namespace std;

string normalizeText(string s)
{
    // lowercase
    transform(
        s.begin(),
        s.end(),
        s.begin(),
        [](unsigned char c)
        {
            return tolower(c);
        });

    // trim + collapse spaces
    stringstream ss(s);
    string word;
    string result;

    while (ss >> word)
    {
        if (!result.empty())
            result += " ";

        result += word;
    }

    return result;
}

void normalizeField(json& obj, const string& key)
{
    if (obj.contains(key) && obj[key].is_string())
    {
        obj[key] = normalizeText(obj[key]);
    }
}

int main()
{
    ifstream in("candidates.jsonl");
    ofstream out("cleaned_candidates.jsonl");

    if (!in.is_open())
    {
        cerr << "Cannot open input file\n";
        return 1;
    }

    string line;
    long long count = 0;

    while (getline(in, line))
    {
        if (line.empty())
            continue;

        json candidate = json::parse(line);

        // ------------------------
        // profile
        // ------------------------
        auto& profile = candidate["profile"];

        normalizeField(profile, "headline");
        normalizeField(profile, "summary");
        normalizeField(profile, "current_title");
        normalizeField(profile, "current_company");
        normalizeField(profile, "current_industry");
        normalizeField(profile, "location");
        normalizeField(profile, "country");

        // ------------------------
        // career_history
        // ------------------------
        for (auto& job : candidate["career_history"])
        {
            normalizeField(job, "company");
            normalizeField(job, "title");
            normalizeField(job, "industry");
            normalizeField(job, "description");
        }

        // ------------------------
        // education
        // ------------------------
        for (auto& edu : candidate["education"])
        {
            normalizeField(edu, "institution");
            normalizeField(edu, "degree");
            normalizeField(edu, "field_of_study");
        }

        // ------------------------
        // skills
        // ------------------------
        for (auto& skill : candidate["skills"])
        {
            normalizeField(skill, "name");
            normalizeField(skill, "proficiency");
        }

        // ------------------------
        // certifications
        // ------------------------
        if (candidate.contains("certifications"))
        {
            for (auto& cert : candidate["certifications"])
            {
                normalizeField(cert, "name");
                normalizeField(cert, "issuer");
            }
        }

        // ------------------------
        // languages
        // ------------------------
        if (candidate.contains("languages"))
        {
            for (auto& lang : candidate["languages"])
            {
                normalizeField(lang, "language");
                normalizeField(lang, "proficiency");
            }
        }

        out << candidate.dump() << '\n';

        count++;
    }

    cout << "Processed: " << count << " candidates\n";

    in.close();
    out.close();

    return 0;
}